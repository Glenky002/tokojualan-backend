from django.core.management.base import BaseCommand
from store.models import Category, Supplier, Product

class Command(BaseCommand):
    help = 'Mengisi database dengan 20 produk dummy otomatis'

    def handle(self, *args, **kwargs):
        self.stdout.write('Sedang meracik data supplier dan kategori...')

        # 1. Buat Kategori
        cat_makanan, _ = Category.objects.get_or_create(name='Makanan & Snack')
        cat_minuman, _ = Category.objects.get_or_create(name='Minuman Segar')
        cat_pakaian, _ = Category.objects.get_or_create(name='Pakaian')
        cat_aksesoris, _ = Category.objects.get_or_create(name='Aksesoris & Gadget')

        # 2. Buat Supplier Default
        supplier_utama, _ = Supplier.objects.get_or_create(
            name='Supplier Utama Toko', 
            defaults={'description': 'Supplier pusat aneka barang'}
        )

        # 3. Data 20 Produk
        dummy_products = [
            {"name": "Keripik Singkong Balado Extra Pedas", "category": cat_makanan, "purchase_price": 8000, "selling_price": 12000, "stock": 50},
            {"name": "Mie Gepeng Makaroni Renyah", "category": cat_makanan, "purchase_price": 5000, "selling_price": 8000, "stock": 40},
            {"name": "Kacang Garuda Pilus Sapi", "category": cat_makanan, "purchase_price": 4000, "selling_price": 7000, "stock": 60},
            {"name": "Basreng Daun Jeruk Pedas Gila", "category": cat_makanan, "purchase_price": 7000, "selling_price": 11000, "stock": 35},
            {"name": "Chocolate Cookies Crunchy Box", "category": cat_makanan, "purchase_price": 15000, "selling_price": 22000, "stock": 25},
            {"name": "Kopi Susu Gula Aren Literan", "category": cat_minuman, "purchase_price": 18000, "selling_price": 25000, "stock": 20},
            {"name": "Es Teh Manis Jasmine Cup", "category": cat_minuman, "purchase_price": 3000, "selling_price": 5000, "stock": 100},
            {"name": "Susu Cokelat Belgian Botol 350ml", "category": cat_minuman, "purchase_price": 9000, "selling_price": 15000, "stock": 45},
            {"name": "Matcha Latte Creamy Series", "category": cat_minuman, "purchase_price": 12000, "selling_price": 18000, "stock": 30},
            {"name": "Lemon Tea Segar Dingin", "category": cat_minuman, "purchase_price": 4000, "selling_price": 7000, "stock": 50},
            {"name": "Kaos Polos Hitam Cotton Combed 30s", "category": cat_pakaian, "purchase_price": 35000, "selling_price": 65000, "stock": 15},
            {"name": "Hoodie Oversize Fleece Abu-abu", "category": cat_pakaian, "purchase_price": 90000, "selling_price": 145000, "stock": 10},
            {"name": "Kemeja Flanel Kotak-kotak Casual", "category": cat_pakaian, "purchase_price": 60000, "selling_price": 95000, "stock": 12},
            {"name": "Topi Baseball Cap Bordir Premium", "category": cat_pakaian, "purchase_price": 20000, "selling_price": 35000, "stock": 25},
            {"name": "Celana Jogger Pants Fleece Sport", "category": cat_pakaian, "purchase_price": 55000, "selling_price": 85000, "stock": 18},
            {"name": "Kabel Data Fast Charging Type-C 1M", "category": cat_aksesoris, "purchase_price": 15000, "selling_price": 30000, "stock": 40},
            {"name": "TWS Bluetooth Earbuds Wireless V5.3", "category": cat_aksesoris, "purchase_price": 75000, "selling_price": 135000, "stock": 12},
            {"name": "Holder HP Meja Lipat Aluminium", "category": cat_aksesoris, "purchase_price": 12000, "selling_price": 25000, "stock": 30},
            {"name": "Powerbank Mini 10000mAh Fast Charge", "category": cat_aksesoris, "purchase_price": 95000, "selling_price": 160000, "stock": 8},
            {"name": "Tempered Glass Layar Universal 9H", "category": cat_aksesoris, "purchase_price": 8000, "selling_price": 15000, "stock": 50},
        ]

        for item in dummy_products:
            Product.objects.get_or_create(
                name=item["name"],
                defaults={
                    "category": item["category"],
                    "supplier": supplier_utama,
                    "purchase_price": item["purchase_price"],
                    "selling_price": item["selling_price"],
                    "stock": item["stock"],
                    "minimum_stock": 5
                }
            )

        self.stdout.write(self.style.SUCCESS('Mantap! 20 produk dummy berhasil dimasukkan via command. 🎉'))