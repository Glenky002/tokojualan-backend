from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import register_user, CustomTokenObtainPairView,promote_to_staff, list_users,get_user_profile,delete_user,admin_change_password,toggle_user_status,ShippingAddressViewSet,change_password
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
router.register(r'shipping-addresses', ShippingAddressViewSet, basename='shipping-address')

urlpatterns = [
    path('register/', register_user, name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Endpoint baru untuk Manajemen User oleh Admin
    path('users/', list_users, name='list-users'),
    path('users/<int:user_id>/promote/', promote_to_staff, name='promote-user'),
    path('auth/user-profile/', get_user_profile, name='user-profile'),

    path('users/<int:user_id>/delete/', delete_user, name='delete_user'),
    path('users/<int:user_id>/change_password/', admin_change_password, name='admin_change_password'),
    path('users/<int:user_id>/toggle-status/', toggle_user_status, name='toggle_user_status'),
    path('auth/change-password/', change_password, name='change-password'),
    
    path('', include(router.urls)),
]