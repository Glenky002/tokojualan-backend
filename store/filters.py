import django_filters
from django.db.models import Q
from .models import Product

class ProductFilter(django_filters.FilterSet):
    # Filter pencarian teks bebas (Nama, SKU, Kategori, Supplier)
    search = django_filters.CharFilter(method='filter_search', label='Search')
    
    # Filter range untuk stok
    stock_min = django_filters.NumberFilter(field_name='stock', lookup_expr='gte')
    stock_max = django_filters.NumberFilter(field_name='stock', lookup_expr='lte')

    # Filter range untuk harga beli (purchase_price)
    purchase_price_min = django_filters.NumberFilter(field_name='purchase_price', lookup_expr='gte')
    purchase_price_max = django_filters.NumberFilter(field_name='purchase_price', lookup_expr='lte')

    # Filter range untuk harga jual (selling_price)
    selling_price_min = django_filters.NumberFilter(field_name='selling_price', lookup_expr='gte')
    selling_price_max = django_filters.NumberFilter(field_name='selling_price', lookup_expr='lte')

    class Meta:
        model = Product
        fields = ['category', 'supplier', 'is_active']

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(name__icontains=value)
            | Q(sku__icontains=value)
            | Q(category__name__icontains=value)
            | Q(supplier__name__icontains=value)
        )