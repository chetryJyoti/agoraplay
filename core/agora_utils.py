"""
Agora utility functions for token generation and RTC/RTM services

This module contains core utilities for working with Agora services.
Can be used across multiple apps (rtc, chat, recording, streaming, etc.)
"""
from django.conf import settings
from agora_token_builder import RtcTokenBuilder
import time


def generate_rtc_token(channel_name, uid=0, expiration_seconds=3600):
    """
    Generate Agora RTC (Real-Time Communication) token for video/audio calls

    This function generates a secure token for accessing Agora RTC channels.
    Tokens are time-limited and should be refreshed before expiration.

    Args:
        channel_name (str): Channel name to join (e.g., "meeting-room-123")
        uid (int): User ID. Use 0 for dynamic assignment by Agora (default: 0)
        expiration_seconds (int): Token validity duration in seconds (default: 3600 = 1 hour)

    Returns:
        dict: Dictionary containing:
            - appId (str): Agora Application ID
            - token (str): Generated RTC token
            - channel (str): Channel name
            - uid (int): User ID

    Raises:
        ValueError: If Agora credentials are not configured in settings

    Example:
        >>> token_data = generate_rtc_token("demo-room", uid=12345)
        >>> print(token_data)
        {
            'appId': 'your_app_id',
            'token': 'generated_token_string',
            'channel': 'demo-room',
            'uid': 12345
        }

    Note:
        For production use, consider implementing token refresh logic
        when the token is about to expire.
    """
    app_id = settings.AGORA_APP_ID
    app_certificate = settings.AGORA_APP_CERTIFICATE

    if not app_id or not app_certificate:
        raise ValueError('Agora credentials not configured in settings')

    # Calculate token expiration time
    current_timestamp = int(time.time())
    privilege_expired_ts = current_timestamp + expiration_seconds

    # Generate RTC token
    # Role: 1 = Publisher (can publish and subscribe to streams)
    # Role: 2 = Subscriber (can only subscribe to streams)
    token = RtcTokenBuilder.buildTokenWithUid(
        app_id,
        app_certificate,
        channel_name,
        uid,
        1,  # Role: Publisher (allows both publishing and subscribing)
        privilege_expired_ts
    )

    return {
        'appId': app_id,
        'token': token,
        'channel': channel_name,
        'uid': uid
    }


# Future: Add RTM token generation for chat
# def generate_rtm_token(user_id, expiration_seconds=3600):
#     """Generate Agora RTM (Real-Time Messaging) token for chat"""
#     pass
