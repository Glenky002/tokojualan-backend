from django.contrib.auth import get_user_model # <--- GUNAKAN INI
from rest_framework import status 
from rest_framework.response import Response
from rest_framework.permissions import AllowAny,IsAdminUser
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view, permission_classes, parser_classes
from .models import UserProfile # Sesuaikan dengan model profil Anda

User = get_user_model() # <--- MENDAPATKAN MODEL USER YANG AKTIF (CustomUser)

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    try:
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email', '')

        if not username or not password:
            return Response({"detail": "Username dan password wajib diisi."}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({"detail": "Username sudah terdaftar."}, status=status.HTTP_400_BAD_REQUEST)

        # Membuat user menggunakan CustomUser model yang aktif
        user = User.objects.create_user(username=username, password=password, email=email)
        
        # Cek apakah field 'is_staff' ada di CustomUser Anda (biasanya bawaan AbstractUser sudah ada)
        if hasattr(user, 'is_staff'):
            user.is_staff = False  
            user.save()

        return Response({"detail": "Registrasi berhasil! Silakan login."}, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def promote_to_staff(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        user.is_staff = True  # Ubah status menjadi pegawai/admin
        user.save()
        return Response({"detail": f"User {user.username} berhasil diangkat menjadi pegawai."})
    except User.DoesNotExist:
        return Response({"detail": "User tidak ditemukan."}, status=404)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_users(request):
    """Opsional: Mengambil daftar semua user agar admin bisa melihat siapa saja yang terdaftar"""
    users = User.objects.all().values('id', 'username', 'email', 'is_staff')
    return Response(list(users))

@api_view(['GET', 'PUT']) # <--- 1. Pastikan 'PUT' ada di sini!
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser]) # <--- Wajib agar bisa baca file upload
def get_user_profile(request):
    # Ambil atau buat profil jika belum ada
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'GET':
        return Response({
            "name": request.user.get_full_name() or request.user.username,
            "email": request.user.email,
            "role": "admin" if request.user.is_staff else "customer",
            "avatar": request.build_absolute_uri(profile.avatar.url) if profile.avatar else None
        })

    elif request.method == 'PUT':
        avatar_file = request.FILES.get('avatar')
        if avatar_file:
            profile.avatar = avatar_file
            profile.save()
            
        return Response({
            "message": "Foto profil berhasil diperbarui!",
            "avatar": request.build_absolute_uri(profile.avatar.url) if profile.avatar else None
        })