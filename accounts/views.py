from django.contrib.auth import get_user_model # <--- GUNAKAN INI
from rest_framework import status 
from rest_framework.response import Response
from rest_framework.permissions import AllowAny,IsAdminUser
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view, permission_classes, parser_classes,action
from .models import UserProfile,CustomUser # Sesuaikan dengan model profil Anda,
from rest_framework.pagination import PageNumberPagination

User = get_user_model() # <--- MENDAPATKAN MODEL USER YANG AKTIF (CustomUser)


class UserPagination(PageNumberPagination):
    page_size = 10  # 2 data per halaman
    page_size_query_param = 'page_size'

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
    # Gunakan QuerySet model standar (jangan .values()) agar bisa diproses paginator & serializer dengan mulus
    users = CustomUser.objects.all().order_by('-date_joined')
    
    paginator = UserPagination()
    result_page = paginator.paginate_queryset(users, request)
    
    if result_page is not None:
        # Jika kamu punya UserSerializer, gunakan ini:
        # serializer = UserSerializer(result_page, many=True)
        # return paginator.get_paginated_response(serializer.data)
        
        # ATAU jika ingin manual tanpa file Serializer terpisah tapi tetap ter-paginate:
        data = [{
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "is_staff": u.is_staff,
            "is_active": u.is_active
        } for u in result_page]
        
        return paginator.get_paginated_response(data)
    
    # Fallback jika paginasi tidak aktif
    data = [{
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "is_staff": u.is_staff,
        "is_active": u.is_active
    } for u in users]
    return Response(data)

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

@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_user(request, user_id):
    """Menghapus akun pengguna berdasarkan ID (Hanya Admin)"""
    try:
        user = User.objects.get(id=user_id)
        
        # Mencegah admin menghapus akunnya sendiri secara tidak sengaja
        if user == request.user:
            return Response({"detail": "Anda tidak dapat menghapus akun Anda sendiri."}, status=status.HTTP_400_BAD_REQUEST)
            
        user.delete()
        return Response({"detail": "Pengguna berhasil dihapus."}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({"detail": "User tidak ditemukan."}, status=status.HTTP_404_NOT_FOUND)


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def admin_change_password(request, user_id):
    """Mengubah password pengguna lain oleh Admin"""
    try:
        user = User.objects.get(id=user_id)
        new_password = request.data.get('password')
        
        if not new_password or len(new_password) < 6:
            return Response({"detail": "Password baru wajib diisi dan minimal 6 karakter."}, status=status.HTTP_400_BAD_REQUEST)
            
        user.set_password(new_password)
        user.save()
        return Response({"detail": f"Password untuk {user.username} berhasil diubah."}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({"detail": "User tidak ditemukan."}, status=status.HTTP_404_NOT_FOUND)

@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def toggle_user_status(request, user_id):
    """Menonaktifkan (suspend) atau mengaktifkan kembali akun pengguna (Hanya Admin)"""
    try:
        user = User.objects.get(id=user_id)
        
        # Mencegah admin menonaktifkan akun sendiri
        if user == request.user:
            return Response({"detail": "Anda tidak dapat menonaktifkan akun Anda sendiri."}, status=status.HTTP_400_BAD_REQUEST)
            
        # Balik status is_active (kalau True jadi False, kalau False jadi True)
        user.is_active = not user.is_active
        user.save()
        
        status_text = "diaktifkan" if user.is_active else "dinonaktifkan (suspend)"
        return Response({"detail": f"Akun {user.username} berhasil {status_text}."}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({"detail": "User tidak ditemukan."}, status=status.HTTP_404_NOT_FOUND)

