from rest_framework import serializers
from accounts.models import ShippingAddress
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
    
    # Kita buat properti custom agar mudah dibaca di React
    whatsapp_number = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ['invoice_number', 'created_at']

    def get_whatsapp_number(self, obj):
        # Mengambil langsung dari kolom customer_phone yang ada di model Transaction Anda
        if obj.customer_phone:
            return str(obj.customer_phone).strip()
        return None

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        transaction = Transaction.objects.create(**validated_data)
        
        for item_data in items_data:
            product = item_data.get('product')
            qty = item_data.get('quantity', 1)
            
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

# class OrderItemSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = OrderItem
#         fields = ['id', 'product_name', 'price', 'quantity']

# class OrderSerializer(serializers.ModelSerializer):
#     items = OrderItemSerializer(many=True, read_only=True)
#     username = serializers.CharField(source='user.username', read_only=True)

#     class Meta:
#         model = Order
#         fields = ['id', 'username', 'total_price', 'status', 'shipping_address', 'whatsapp_number', 'created_at', 'items']
#         read_only_fields = ['user', 'total_price']