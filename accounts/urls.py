from django.urls import path
from .views import register_user, CustomTokenObtainPairView,promote_to_staff, list_users,get_user_profile
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/', register_user, name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Endpoint baru untuk Manajemen User oleh Admin
    path('users/', list_users, name='list-users'),
    path('users/<int:user_id>/promote/', promote_to_staff, name='promote-user'),
    path('auth/user-profile/', get_user_profile, name='user-profile'),
]