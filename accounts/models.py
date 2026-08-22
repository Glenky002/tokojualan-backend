from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db import models
from django.conf import settings # <--- 1. Import settings

class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_admin_store = models.BooleanField(default=False) # Penanda apakah user ini admin toko

    def __str__(self):
        return self.username

class UserProfile(models.Model):
    # 2. Gunakan settings.AUTH_USER_MODEL alih-alih auth.User
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    
    def __str__(self):
        return f"Profil {self.user.username}"