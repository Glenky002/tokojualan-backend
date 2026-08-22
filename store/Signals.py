# products/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Product, ProductHistory

@receiver(post_save, sender=Product)
def log_product_save(sender, instance, created, **kwargs):
    action = 'CREATE' if created else 'UPDATE'
    ProductHistory.objects.create(
        product_name=instance.name,
        action=action,
        details=f"Stok: {instance.stock}, Harga Jual: {instance.selling_price}"
    )

@receiver(post_delete, sender=Product)
def log_product_delete(sender, instance, **kwargs):
    ProductHistory.objects.create(
        product_name=instance.name,
        action='DELETE',
        details="Produk dihapus dari sistem"
    )