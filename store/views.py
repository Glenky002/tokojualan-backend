from decimal import Decimal, InvalidOperation
from django.db.models import Q, F
from rest_framework import viewsets, status
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
    ProductHistorySerializer
)
from .filters import ProductFilter
import pandas as pd


class ProductHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProductHistory.objects.all().order_by('-timestamp')
    serializer_class = ProductHistorySerializer

class ProductPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


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


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated or not user.is_staff:
            return Transaction.objects.none()
        return Transaction.objects.all().order_by('-created_at')

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(cashier=self.request.user)
        else:
            serializer.save()


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class SupplierViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated]
