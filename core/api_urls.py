"""
Core Agora API endpoints

These APIs provide Agora services (tokens, recording, etc.)
for use by all apps and external clients.
"""
from django.urls import path
from . import api_views

app_name = 'agora_api'

urlpatterns = [
    # RTC token generation
    path('token/', api_views.get_rtc_token, name='rtc_token'),

    # Cloud Recording endpoints
    path('recording/start/', api_views.start_recording, name='start_recording'),
    path('recording/stop/', api_views.stop_recording, name='stop_recording'),
    path('recording/query/', api_views.query_recording, name='query_recording'),

    # Future endpoints:
    # path('rtm/token/', api_views.get_rtm_token, name='rtm_token'),
]
