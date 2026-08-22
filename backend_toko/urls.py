from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('store.urls')), # Semua API akan diawali dengan /api/
    path('api/auth/', include('accounts.urls')),
    path('api/', include('accounts.urls')), # <--- Pastikan ada prefix 'api/'
]

# Tambahkan baris ini agar file gambar bisa diakses saat mode development (runserver)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)