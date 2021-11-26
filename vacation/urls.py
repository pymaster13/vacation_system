from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('client.urls')),
    path('admin/', include('admin_app.urls')),
    path('admin_panel/', admin.site.urls),
]
