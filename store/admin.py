from django.contrib import admin
from .models import Category, Supplier, Product, Transaction, TransactionItem

class TransactionItemInline(admin.TabularInline):
    model = TransactionItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'price_at_sale']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['sku', 'name', 'category', 'supplier', 'selling_price', 'stock', 'is_active']
    list_filter = ['is_active', 'category', 'supplier']
    search_fields = ['name', 'sku']
    readonly_fields = ['sku', 'created_at', 'updated_at']

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'customer_name', 'customer_phone', 'total_amount', 'status', 'order_type', 'created_at']
    list_filter = ['status', 'order_type', 'created_at']
    search_fields = ['invoice_number', 'customer_name', 'customer_phone']
    inlines = [TransactionItemInline]
    readonly_fields = ['invoice_number', 'total_amount', 'created_at']