"""
Core API views for Agora services

These APIs are shared across all features (RTC, RTM, Recording, Streaming)
and can be consumed by web clients, mobile apps, and external services.
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .agora_utils import (
    generate_rtc_token,
    acquire_recording_resource,
    start_cloud_recording,
    stop_cloud_recording,
    query_cloud_recording
)


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


# ============================================================================
# Cloud Recording API Endpoints
# ============================================================================

@api_view(['POST'])
def start_recording(request):
    """
    Start cloud recording for a channel

    This endpoint handles both acquire and start steps of cloud recording.

    Request Body:
        {
            "channel": "channel-name",
            "uid": "999999",  # Recording service UID (must be unique integer)
            "mode": "mix"     # optional: "mix" or "individual" (default: "mix")
        }

    Response:
        {
            "resourceId": "...",
            "sid": "...",
            "message": "Recording started successfully"
        }

    Example:
        POST /api/recording/start/
        {
            "channel": "demo-room",
            "uid": "999999"
        }
    """
    channel = request.data.get('channel')
    uid = request.data.get('uid')
    mode = request.data.get('mode', 'mix')

    if not channel:
        return Response(
            {'error': 'channel parameter is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not uid:
        return Response(
            {'error': 'uid parameter is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Step 1: Acquire recording resource
        acquire_response = acquire_recording_resource(channel, uid)
        resource_id = acquire_response.get('resourceId')

        if not resource_id:
            return Response(
                {'error': 'Failed to acquire recording resource'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Step 2: Generate token for recording service
        token_data = generate_rtc_token(channel, int(uid))
        token = token_data['token']

        # Step 3: Start recording
        start_response = start_cloud_recording(
            resource_id, channel, uid, token, mode
        )

        return Response({
            'resourceId': resource_id,
            'sid': start_response.get('sid'),
            'message': 'Recording started successfully'
        })

    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        return Response(
            {'error': f'Failed to start recording: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def stop_recording(request):
    """
    Stop cloud recording

    Request Body:
        {
            "resourceId": "...",
            "sid": "...",
            "channel": "channel-name",
            "uid": "999999",
            "mode": "mix"  # optional: must match the mode used in start
        }

    Response:
        {
            "serverResponse": {...},
            "message": "Recording stopped successfully"
        }

    Example:
        POST /api/recording/stop/
        {
            "resourceId": "xyz123",
            "sid": "abc456",
            "channel": "demo-room",
            "uid": "999999"
        }
    """
    resource_id = request.data.get('resourceId')
    sid = request.data.get('sid')
    channel = request.data.get('channel')
    uid = request.data.get('uid')
    mode = request.data.get('mode', 'mix')

    if not all([resource_id, sid, channel, uid]):
        return Response(
            {'error': 'resourceId, sid, channel, and uid are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        stop_response = stop_cloud_recording(
            resource_id, sid, channel, uid, mode
        )

        return Response({
            'serverResponse': stop_response.get('serverResponse'),
            'message': 'Recording stopped successfully'
        })

    except Exception as e:
        return Response(
            {'error': f'Failed to stop recording: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def query_recording(request):
    """
    Query cloud recording status

    Query Parameters:
        - resourceId (required): Resource ID from start recording
        - sid (required): Session ID from start recording
        - mode (optional): Recording mode (default: "mix")

    Response:
        {
            "serverResponse": {...},
            "status": "..."
        }

    Example:
        GET /api/recording/query/?resourceId=xyz123&sid=abc456
    """
    resource_id = request.GET.get('resourceId')
    sid = request.GET.get('sid')
    mode = request.GET.get('mode', 'mix')

    if not resource_id or not sid:
        return Response(
            {'error': 'resourceId and sid parameters are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        query_response = query_cloud_recording(resource_id, sid, mode)

        return Response({
            'serverResponse': query_response.get('serverResponse'),
            'status': 'Recording is active'
        })

    except Exception as e:
        return Response(
            {'error': f'Failed to query recording: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Future API endpoints for other Agora services:

# @api_view(['GET'])
# def get_rtm_token(request):
#     """Generate Agora RTM token for chat/messaging"""
#     pass
