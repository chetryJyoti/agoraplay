from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Web views (HTML pages)
    path('rtc/', include('rtc.urls')),

    # Core Agora API endpoints (for mobile apps, external services, all features)
    path('api/agora/', include('core.api_urls')),
]
