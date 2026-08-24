from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_admin_store = models.BooleanField(default=False)

    def __str__(self):
        return self.username

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    whatsapp = models.CharField(max_length=20, blank=True, null=True) # <-- Tambah ini
    address = models.TextField(blank=True, null=True)                 # <-- Tambah ini
    
    def __str__(self):
        return f"Profil {self.user.username}"


class ShippingAddress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shipping_addresses')
    recipient_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    address_line = models.TextField()
    city = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=10, blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Jika alamat ini diset sebagai default, matikan default alamat lain milik user yang sama
        if self.is_default:
            ShippingAddress.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.recipient_name} - {self.address_line[:30]}..."