from decimal import Decimal, InvalidOperation
from django.db.models import Q, F
from rest_framework import viewsets, status,filters
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Product, Category, Supplier, Transaction,ProductHistory
from .serializers import (
    ProductSerializer, 
    CategorySerializer, 
    SupplierSerializer, 
    TransactionSerializer,
    ProductHistorySerializer,
)
from .filters import ProductFilter
import pandas as pd


class ProductPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

class ProductHistoryViewSet(viewsets.ModelViewSet):
    queryset = ProductHistory.objects.all().order_by('-timestamp')
    serializer_class = ProductHistorySerializer
    pagination_class = ProductPagination # Sesuaikan dengan nama kelas pagination Anda

    filter_backends = [filters.SearchFilter]
    search_fields = ['product_name', 'details', 'action', 'user__username'] # Kolom yang bisa dicari

    def get_queryset(self):
        queryset = super().get_queryset()
        action_param = self.request.query_params.get('action', None)
        
        if action_param:
            sel = action_param.lower()
            if sel == 'tambah':
                queryset = queryset.filter(
                    Q(action__icontains='tambah') | 
                    Q(action__icontains='create') | 
                    Q(action__icontains='add') |
                    Q(action__icontains='post')
                )
            elif sel == 'ubah':
                queryset = queryset.filter(
                    Q(action__icontains='ubah') | 
                    Q(action__icontains='update') | 
                    Q(action__icontains='edit') |
                    Q(action__icontains='put')
                )
            elif sel == 'hapus':
                queryset = queryset.filter(
                    Q(action__icontains='hapus') | 
                    Q(action__icontains='delete')
                )
            else:
                queryset = queryset.filter(action__icontains=action_param)
                
        return queryset

    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        ids = request.data.get('ids', [])
        if not ids:
            return Response({"error": "Tidak ada ID yang dipilih."}, status=400)
        
        ProductHistory.objects.filter(id__in=ids).delete()
        return Response({"message": f"Berhasil menghapus {len(ids)} riwayat aktivitas."}, status=200)



class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category", "supplier").all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    pagination_class = ProductPagination  # <--- Pastikan ini aktif
    filterset_class = ProductFilter  # Hubungkan ke ProductFilter

    @action(detail=False, methods=['post'])
    def import_data(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({"detail": "Tidak ada file yang diunggah"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Deteksi format file (CSV atau Excel)
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)

            # Normalisasi nama kolom (ubah ke lowercase dan hapus spasi berlebih)
            df.columns = df.columns.str.strip().str.lower()

            success_count = 0
            error_rows = []

            for index, row in df.iterrows():
                try:
                    # Ambil data dengan beberapa alternatif nama kolom
                    name = row.get('nama produk') or row.get('name')
                    selling_price = row.get('harga jual') or row.get('selling_price') or row.get('price') or 0
                    purchase_price = row.get('harga beli') or row.get('purchase_price') or (selling_price * 0.8)
                    stock = row.get('stok') or row.get('stock') or 0
                    cat_name = row.get('kategori') or row.get('category')
                    supp_name = row.get('supplier') or row.get('supplier_name')

                    if not name or pd.isna(name):
                        continue

                    # 1. Get or Create Kategori (Otomatis buat baru jika belum ada)
                    category = None
                    if cat_name and not pd.isna(cat_name):
                        category, _ = Category.objects.get_or_create(name=str(cat_name).strip())
                    else:
                        category = Category.objects.first()

                    # 2. Get or Create Supplier (Otomatis buat baru jika belum ada)
                    supplier = None
                    if supp_name and not pd.isna(supp_name):
                        supplier, _ = Supplier.objects.get_or_create(name=str(supp_name).strip())
                    else:
                        supplier = Supplier.objects.first()

                    if not category or not supplier:
                        error_rows.append(f"Baris {index+2}: Kategori atau Supplier tidak valid.")
                        continue

                    # Simpan atau Update produk (SKU digenerate otomatis di method save() model)
                    Product.objects.update_or_create(
                        name=str(name).strip(),
                        defaults={
                            'selling_price': selling_price,
                            'purchase_price': purchase_price,
                            'stock': int(stock),
                            'category': category,
                            'supplier': supplier,
                        }
                    )
                    success_count += 1

                except Exception as row_err:
                    error_rows.append(f"Baris {index+2}: {str(row_err)}")

            if success_count == 0 and error_rows:
                return Response({"detail": "Gagal: " + " | ".join(error_rows[:2])}, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                "detail": f"Berhasil mengimpor {success_count} produk!" + (f" ({len(error_rows)} baris dilewati)" if error_rows else "")
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"detail": f"Gagal membaca file: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def activate(self, request, pk=None):
        product = self.get_object()
        product.is_active = True
        product.save()
        return Response({
            "message": "Product berhasil diaktifkan.",
            "id": product.id,
            "is_active": product.is_active,
        })

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def deactivate(self, request, pk=None):
        product = self.get_object()
        product.is_active = False
        product.save()
        return Response({
            "message": "Product berhasil dinonaktifkan.",
            "id": product.id,
            "is_active": product.is_active,
        })

    @action(detail=False, methods=["get"], url_path="low-stock")
    def low_stock(self, request):
        queryset = self.get_queryset().filter(stock__lte=F("minimum_stock"))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def bulk_delete(self, request):
        ids = request.data.get('ids', [])
        if not ids:
            return Response({"detail": "Tidak ada ID produk yang dipilih."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Hapus produk berdasarkan list ID yang dikirim
            deleted_count, _ = Product.objects.filter(id__in=ids).delete()
            return Response({
                "detail": f"Berhasil menghapus {deleted_count} produk!"
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": f"Gagal menghapus produk: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = ProductPagination  # <--- INTEGRASI PAGINATION DI SINI

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Transaction.objects.none()
        
        # 1. Tentukan queryset dasar berdasarkan hak akses user
        if user.is_staff:
            queryset = Transaction.objects.all().order_by('-created_at')
        else:
            queryset = Transaction.objects.filter(cashier=user).order_by('-created_at')

        # 2. Logika filter berdasarkan status (jika ada parameter ?status=...)
        status_param = self.request.query_params.get('status', None)
        if status_param and status_param != 'All':
            queryset = queryset.filter(status__iexact=status_param)

        return queryset

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(cashier=self.request.user) 
        else:
            serializer.save()

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        transaction = self.get_object()
        new_status = request.data.get('status')
        
        valid_statuses = ['Belum Bayar', 'Diproses', 'Dikirim', 'Selesai', 'Batal']
        if new_status not in valid_statuses:
            return Response(
                {"error": "Status tidak valid."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        old_status = transaction.status

        # ---> LOGIKA RESTOCK OTOMATIS SAAT BATAL <---
        if new_status == 'Batal' and old_status != 'Batal':
            for item in transaction.items.all():
                product = item.product
                product.stock += item.quantity  # Stok produk dikembalikan
                product.save()

        elif old_status == 'Batal' and new_status != 'Batal':
            for item in transaction.items.all():
                product = item.product
                if product.stock >= item.quantity:
                    product.stock -= item.quantity
                    product.save()
                else:
                    return Response(
                        {"error": f"Stok produk {product.name} tidak mencukupi untuk membatalkan status batal."}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

        transaction.status = new_status
        transaction.save()
        
        return Response(
            {"message": "Status pesanan berhasil diperbarui dan stok disesuaikan!", "status": transaction.status}, 
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['patch'])
    def cancel_order(self, request, pk=None):
        transaction = self.get_object()

        if transaction.status == 'Batal':
            return Response(
                {"message": "Pesanan ini sudah dibatalkan sebelumnya."}, 
                status=status.HTTP_200_OK
            )

        # Kembalikan stok produk
        for item in transaction.items.all():
            product = item.product
            product.stock += item.quantity
            product.save()

        transaction.status = 'Batal'
        transaction.save()

        return Response(
            {"message": "Pesanan berhasil dibatalkan dan stok produk telah dikembalikan."}, 
            status=status.HTTP_200_OK
        )

    # ---> ACTION UNTUK BULK DELETE PESANAN <---
    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        ids = request.data.get('ids', [])
        if not ids:
            return Response({"error": "Tidak ada ID pesanan yang dipilih."}, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        if user.is_staff:
            deleted_count, _ = Transaction.objects.filter(id__in=ids).delete()
        else:
            deleted_count, _ = Transaction.objects.filter(id__in=ids, cashier=user).delete()

        return Response(
            {"message": f"Berhasil menghapus {deleted_count} data pesanan terpilih."}, 
            status=status.HTTP_200_OK
        )

# class OrderViewSet(viewsets.ModelViewSet):
#     serializer_class = OrderSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         user = self.request.user
#         # Jika user adalah admin (is_staff), tampilkan semua pesanan toko
#         if user.is_staff:
#             return Order.objects.all().order_by('-created_at')
#         # Jika pembeli biasa, hanya tampilkan pesanan miliknya sendiri
#         return Order.objects.filter(user=user).order_by('-created_at')

#     def perform_create(self, serializer):
#         # Saat customer checkout, tangkap data items dari request body secara manual
#         items_data = self.request.data.get('items', [])
#         total_price = 0

#         for item in items_data:
#             total_price += Decimal(str(item.get('price', 0))) * int(item.get('quantity', 1))

#         # Simpan order utama atas nama user yang sedang login
#         order = serializer.save(user=self.request.user, total_price=total_price)

#         # Simpan detail item produk yang dibeli
#         for item in items_data:
#             OrderItem.objects.create(
#                 order=order,
#                 product_name=item.get('product_name'),
#                 price=item.get('price'),
#                 quantity=item.get('quantity')
#             )

#     @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated])
#     def update_status(self, request, pk=None):
#         """Action khusus admin untuk mengubah status pesanan (Pending -> Processing -> Shipped -> Completed)"""
#         if not request.user.is_staff:
#             return Response({"detail": "Anda tidak memiliki izin untuk mengubah status pesanan."}, status=status.HTTP_403_FORBIDDEN)
        
#         order = self.get_object()
#         new_status = request.data.get('status')

#         valid_statuses = [choice[0] for choice in Order.STATUS_CHOICES]
#         if new_status not in valid_statuses:
#             return Response({"detail": "Status pesanan tidak valid."}, status=status.HTTP_400_BAD_REQUEST)

#         order.status = new_status
#         order.save()
        
#         return Response({
#             "message": f"Status order #{order.id} berhasil diubah ke {new_status}!",
#             "status": order.status
#         })
    
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class SupplierViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated]
