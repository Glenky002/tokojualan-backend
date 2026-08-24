from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, CategoryViewSet, SupplierViewSet, TransactionViewSet,ProductHistoryViewSet

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'suppliers', SupplierViewSet, basename='supplier')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'history', ProductHistoryViewSet, basename='product-history') # <-- Pastikan ini a

urlpatterns = [
    # ... url lainnya ...
] + router.urls