"""
RTC views - Web interface for video/audio calls

Note: API endpoints are now in core.api_views
"""
from django.shortcuts import render


def demo(request):
    """Render the video call demo page"""
    return render(request, 'rtc/demo.html')


def recordings(request):
    """Render the recordings viewer page"""
    return render(request, 'rtc/recordings.html')
