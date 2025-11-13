"""
Core API views for Agora services

These APIs are shared across all features (RTC, RTM, Recording, Streaming)
and can be consumed by web clients, mobile apps, and external services.
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .agora_utils import generate_rtc_token


@api_view(['GET'])
def get_rtc_token(request):
    """
    Generate Agora RTC token for video/audio calls

    This endpoint is used by:
    - Web clients (demo page)
    - Mobile apps (iOS, Android)
    - External services

    Query Parameters:
        - channel (required): Channel name to join
        - uid (optional): User ID (default: 0 for dynamic assignment)

    Returns:
        JSON response with appId, token, channel, and uid

    Example:
        GET /api/agora/token/?channel=demo&uid=12345

        Response:
        {
            "appId": "your_app_id",
            "token": "generated_token",
            "channel": "demo",
            "uid": 12345
        }
    """
    # Get channel name from query params
    channel = request.GET.get('channel')

    if not channel:
        return Response(
            {'error': 'channel parameter is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Get optional UID (default to 0 for dynamic assignment)
    try:
        uid = int(request.GET.get('uid', 0))
    except ValueError:
        return Response(
            {'error': 'uid must be a valid integer'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Generate token using core utility function
        token_data = generate_rtc_token(channel, uid)
        return Response(token_data)

    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        return Response(
            {'error': f'Failed to generate token: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Future API endpoints for other Agora services:

# @api_view(['GET'])
# def get_rtm_token(request):
#     """Generate Agora RTM token for chat/messaging"""
#     pass

# @api_view(['POST'])
# def start_recording(request):
#     """Start cloud recording for a channel"""
#     pass

# @api_view(['POST'])
# def stop_recording(request):
#     """Stop cloud recording"""
#     pass
