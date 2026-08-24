from django.db import models
from django.conf import settings  # <--- Pastikan baris ini ada di paling atas!
from django.db.models import Max
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.contrib.auth.models import User
import uuid

# class Order(models.Model):
#     STATUS_CHOICES = (
#         ('Pending', 'Menunggu Konfirmasi'),
#         ('Processing', 'Sedang Diproses'),
#         ('Shipped', 'Dalam Pengiriman'),
#         ('Completed', 'Selesai'),
#         ('Cancelled', 'Dibatalkan'),
#     )

#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
#     total_price = models.DecimalField(max_digits=12, decimal_places=2)
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
#     shipping_address = models.TextField(blank=True, null=True)
#     whatsapp_number = models.CharField(max_length=20, blank=True, null=True)
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"Order #{self.id} - {self.user.username}"

# class OrderItem(models.Model):
#     order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
#     product_name = models.CharField(max_length=255)
#     price = models.DecimalField(max_digits=10, decimal_places=2)
#     quantity = models.PositiveIntegerField()

#     def __str__(self):
#         return f"{self.quantity}x {self.product_name} (Order #{self.order.id})"
    
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]
        verbose_name = "Category"
        verbose_name_plural = "Categories"


class Supplier(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]
        verbose_name = "Supplier"
        verbose_name_plural = "Suppliers"


class Product(models.Model):
    sku = models.CharField(max_length=20, unique=True, blank=True) # Tambahkan blank=True

    def save(self, *args, **kwargs):
        # Jika belum ada SKU, buat otomatis (Contoh: PROD-8d2f)
        if not self.sku:
            self.sku = f"PROD-{uuid.uuid4().hex[:6].upper()}"
        super(Product, self).save(*args, **kwargs)

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    
    purchase_price = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))]
    )
    selling_price = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))]
    )
    
    stock = models.PositiveIntegerField(default=0)
    minimum_stock = models.PositiveIntegerField(default=5)
    
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if (
            self.purchase_price is not None
            and self.selling_price is not None
            and self.selling_price < self.purchase_price
        ):
            raise ValidationError({
                "selling_price": "Harga jual tidak boleh lebih kecil dari harga modal."
            })
        
    def save(self, *args, **kwargs):
        self.full_clean()
        if not self.sku:
            last_product = Product.objects.aggregate(max_id=Max("id"))
            next_id = (last_product["max_id"] or 0) + 1
            self.sku = f"PRD{next_id:06d}"
        super().save(*args, **kwargs)   

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]
        verbose_name = "Product"
        verbose_name_plural = "Products"


class Transaction(models.Model):
    STATUS_CHOICES = [
        ('Belum Bayar', 'Belum Bayar'),
        ('Diproses', 'Diproses'),
        ('Dikirim', 'Dikirim'),
        ('Selesai', 'Selesai'),
        ('Batal', 'Batal'),
    ]

    invoice_number = models.CharField(max_length=50, unique=True, editable=False)
    
    # <--- 2. Ubah dari User ke settings.AUTH_USER_MODEL
    cashier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    customer_name = models.CharField(max_length=255, default="Tamu / Pembeli WA")
    customer_phone = models.CharField(max_length=50, blank=True, null=True)
    shipping_address = models.TextField(blank=True, null=True)
    
    total_amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))]
    )
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Diproses')
    order_type = models.CharField(max_length=50, default='WhatsApp Order') 
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            last_trx = Transaction.objects.aggregate(max_id=Max("id"))
            next_id = (last_trx["max_id"] or 0) + 1
            self.invoice_number = f"INV{next_id:06d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.customer_name}"

    class Meta:
        ordering = ["-created_at"]


class TransactionItem(models.Model):
    transaction = models.ForeignKey(Transaction, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price_at_sale = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))]
    )

    def __str__(self):
        return f"{self.quantity}x {self.product.name if self.product else 'Produk'}"


class ProductHistory(models.Model):
    product_name = models.CharField(max_length=255)
    action = models.CharField(max_length=50) # 'CREATE', 'UPDATE', 'DELETE'
    details = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Perbaikan di sini menggunakan settings.AUTH_USER_MODEL
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL
    )

    def __str__(self):
        return f"{self.action} - {self.product_name} ({self.timestamp})"