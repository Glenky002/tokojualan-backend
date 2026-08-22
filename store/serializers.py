from rest_framework import serializers
from .models import Category, Supplier, Product, Transaction, TransactionItem,ProductHistory

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    supplier_name = serializers.ReadOnlyField(source='supplier.name')

    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['sku', 'created_at', 'updated_at']

class TransactionItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')

    class Meta:
        model = TransactionItem
        fields = ['id', 'product', 'product_name', 'quantity', 'price_at_sale']

class TransactionSerializer(serializers.ModelSerializer):
    items = TransactionItemSerializer(many=True)
    cashier_username = serializers.ReadOnlyField(source='cashier.username')

    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ['invoice_number', 'created_at']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        
        # Buat transaksi utama
        transaction = Transaction.objects.create(**validated_data)
        
        # Proses item dan kurangi stok produk secara otomatis
        for item_data in items_data:
            product = item_data.get('product')
            qty = item_data.get('quantity')
            
            if product:
                if product.stock < qty:
                    raise serializers.ValidationError(f"Stok produk {product.name} tidak mencukupi!")
                product.stock -= qty
                product.save()

            TransactionItem.objects.create(transaction=transaction, **item_data)
            
        return transaction

class ProductHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductHistory
        fields = '__all__'