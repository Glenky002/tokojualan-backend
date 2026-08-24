from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserProfile,ShippingAddress

class ShippingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = [
            'id', 'recipient_name', 'phone_number', 'address_line', 
            'city', 'postal_code', 'latitude', 'longitude', 'is_default'
        ]
        read_only_fields = ['id']

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Masukkan data tambahan ke dalam payload token jika diperlukan
        token['username'] = user.username
        token['is_staff'] = user.is_staff
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Kirim juga data user di respons JSON saat login sukses
        data['username'] = self.user.username
        data['is_staff'] = self.user.is_staff
        data['is_superuser'] = self.user.is_superuser
        return data

User = get_user_model()

class UserProfileSerializer(serializers.ModelSerializer):
    # Field dari CustomUser
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', required=False, allow_blank=True)
    role = serializers.CharField(source='user.is_admin_store', read_only=True) # atau sesuaikan logic role-mu
    
    # Field dari UserProfile
    whatsapp = serializers.CharField(required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    avatar = serializers.ImageField(read_only=True) # Avatar di-handle terpisah/khusus

    class Meta:
        model = UserProfile
        fields = ['username', 'email', 'first_name', 'whatsapp', 'address', 'avatar', 'role']

    def update(self, instance, validated_data):
        # Ambil data user dari nested dictionary 'user'
        user_data = validated_data.pop('user', {})
        first_name = user_data.get('first_name')

        if first_name is not None:
            instance.user.first_name = first_name
            instance.user.save()

        # Update field di model UserProfile (whatsapp, address)
        instance.whatsapp = validated_data.get('whatsapp', instance.whatsapp)
        instance.address = validated_data.get('address', instance.address)
        instance.save()

        return instance

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)