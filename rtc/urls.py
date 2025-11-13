"""
Web URLs for RTC functionality (HTML pages, not APIs)
"""
from django.urls import path
from . import views

app_name = 'rtc'

urlpatterns = [
    path('demo/', views.demo, name='demo'),
]
