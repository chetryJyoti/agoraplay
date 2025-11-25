"""
Agora utility functions for token generation and RTC/RTM services

This module contains core utilities for working with Agora services.
Can be used across multiple apps (rtc, chat, recording, streaming, etc.)
"""
from django.conf import settings
from agora_token_builder import RtcTokenBuilder
import time
import requests
import base64
import json
import boto3
from botocore.exceptions import ClientError


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


# ============================================================================
# Cloud Recording Functions
# ============================================================================

def _get_auth_header():
    """
    Generate Basic Auth header for Agora Cloud Recording API

    Returns:
        dict: Headers with Authorization
    """
    customer_id = settings.AGORA_CUSTOMER_ID
    customer_certificate = settings.AGORA_CUSTOMER_CERTIFICATE

    if not customer_id or not customer_certificate:
        raise ValueError('Agora Customer credentials not configured')

    # Create Basic Auth credentials
    credentials = f"{customer_id}:{customer_certificate}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    return {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/json'
    }


def _get_storage_config():
    """
    Get S3 storage configuration for cloud recording

    Returns:
        dict: Storage configuration
    """
    # AWS S3 vendor code is 1
    # Region must be an integer code for S3
    # Map of AWS region names to Agora region codes
    region_map = {
        'us-east-1': 0,
        'us-east-2': 1,
        'us-west-1': 2,
        'us-west-2': 3,
        'eu-west-1': 4,
        'eu-west-2': 5,
        'eu-west-3': 6,
        'eu-central-1': 7,
        'ap-southeast-1': 8,
        'ap-southeast-2': 9,
        'ap-northeast-1': 10,
        'ap-northeast-2': 11,
        'ap-south-1': 12,
        'ca-central-1': 13,
        'sa-east-1': 14,
        'cn-north-1': 15,
        'cn-northwest-1': 16
    }

    region_code = region_map.get(settings.AWS_S3_REGION_NAME, 12)  # Default to ap-south-1

    return {
        "vendor": 1,
        "region": region_code,
        "bucket": settings.AWS_STORAGE_BUCKET_NAME,
        "accessKey": settings.AWS_ACCESS_KEY_ID,
        "secretKey": settings.AWS_SECRET_ACCESS_KEY
    }


def acquire_recording_resource(channel_name, uid):
    """
    Acquire resource for cloud recording

    This is the first step in starting a cloud recording.
    Resource ID is valid for 5 minutes.

    Args:
        channel_name (str): Channel name to record
        uid (str): Recording service UID (must be unique integer as string)

    Returns:
        dict: Contains resourceId

    Raises:
        Exception: If API request fails
    """
    app_id = settings.AGORA_APP_ID
    url = f"https://api.agora.io/v1/apps/{app_id}/cloud_recording/acquire"

    headers = _get_auth_header()

    payload = {
        "cname": channel_name,
        "uid": uid,
        "clientRequest": {}
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        raise Exception(f"Failed to acquire resource: {response.text}")

    return response.json()


def start_cloud_recording(resource_id, channel_name, uid, token, mode="mix", file_format="mp4"):
    """
    Start cloud recording

    Args:
        resource_id (str): Resource ID from acquire step
        channel_name (str): Channel name to record
        uid (str): Recording service UID (same as acquire)
        token (str): RTC token for the recording service
        mode (str): Recording mode - "individual" or "mix" (default: "mix")
        file_format (str): Output format - "mp4" or "hls" (default: "mp4")

    Returns:
        dict: Contains sid (recording session ID) and resourceId

    Raises:
        Exception: If API request fails
    """
    app_id = settings.AGORA_APP_ID
    url = f"https://api.agora.io/v1/apps/{app_id}/cloud_recording/resourceid/{resource_id}/mode/{mode}/start"

    headers = _get_auth_header()
    storage_config = _get_storage_config()

    # Configure recording file format
    recording_file_config = {}
    if file_format == "mp4":
        # MP4 format - generates a single .mp4 file
        recording_file_config = {
            "avFileType": ["hls", "mp4"]  # Generate both HLS and MP4 for compatibility
        }
    else:
        # HLS format only (default legacy behavior)
        recording_file_config = {
            "avFileType": ["hls"]
        }

    payload = {
        "cname": channel_name,
        "uid": uid,
        "clientRequest": {
            "token": token,
            "recordingConfig": {
                "maxIdleTime": 30,
                "streamTypes": 2,  # 0: audio only, 1: video only, 2: audio and video
                "channelType": 0,  # 0: Communication, 1: Live Broadcast
                "videoStreamType": 0,  # 0: high stream, 1: low stream
                "transcodingConfig": {
                    "width": 1280,
                    "height": 720,
                    "fps": 30,
                    "bitrate": 2000,
                    "mixedVideoLayout": 1  # 0: float, 1: best fit, 2: vertical
                }
            },
            "recordingFileConfig": recording_file_config,
            "storageConfig": storage_config
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        raise Exception(f"Failed to start recording: {response.text}")

    return response.json()


def stop_cloud_recording(resource_id, sid, channel_name, uid, mode="mix"):
    """
    Stop cloud recording

    Args:
        resource_id (str): Resource ID from acquire step
        sid (str): Session ID from start step
        channel_name (str): Channel name
        uid (str): Recording service UID
        mode (str): Recording mode used (default: "mix")

    Returns:
        dict: Contains upload status and file info

    Raises:
        Exception: If API request fails
    """
    app_id = settings.AGORA_APP_ID
    url = f"https://api.agora.io/v1/apps/{app_id}/cloud_recording/resourceid/{resource_id}/sid/{sid}/mode/{mode}/stop"

    headers = _get_auth_header()

    payload = {
        "cname": channel_name,
        "uid": uid,
        "clientRequest": {}
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        raise Exception(f"Failed to stop recording: {response.text}")

    return response.json()


def query_cloud_recording(resource_id, sid, mode="mix"):
    """
    Query cloud recording status

    Args:
        resource_id (str): Resource ID from acquire step
        sid (str): Session ID from start step
        mode (str): Recording mode used (default: "mix")

    Returns:
        dict: Recording status and file information

    Raises:
        Exception: If API request fails
    """
    app_id = settings.AGORA_APP_ID
    url = f"https://api.agora.io/v1/apps/{app_id}/cloud_recording/resourceid/{resource_id}/sid/{sid}/mode/{mode}/query"

    headers = _get_auth_header()

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Failed to query recording: {response.text}")

    return response.json()


# ============================================================================
# S3 Helper Functions for Recording Files
# ============================================================================

def _get_s3_client():
    """Get boto3 S3 client with credentials"""
    return boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME
    )


def list_recording_files(sid):
    """
    List all recording files in S3 for a given session ID

    Args:
        sid (str): Session ID from recording

    Returns:
        dict: {
            'mp4_files': [...],
            'm3u8_files': [...],
            'ts_files': [...],
            'all_files': [...]
        }
    """
    try:
        s3_client = _get_s3_client()
        bucket = settings.AWS_STORAGE_BUCKET_NAME

        # List objects with prefix matching the session ID
        response = s3_client.list_objects_v2(
            Bucket=bucket,
            Prefix=sid
        )

        if 'Contents' not in response:
            return {
                'mp4_files': [],
                'm3u8_files': [],
                'ts_files': [],
                'all_files': []
            }

        all_files = [obj['Key'] for obj in response['Contents']]
        mp4_files = [f for f in all_files if f.endswith('.mp4')]
        m3u8_files = [f for f in all_files if f.endswith('.m3u8')]
        ts_files = [f for f in all_files if f.endswith('.ts')]

        return {
            'mp4_files': mp4_files,
            'm3u8_files': m3u8_files,
            'ts_files': ts_files,
            'all_files': all_files
        }

    except ClientError as e:
        print(f"Error listing S3 files: {e}")
        return {
            'mp4_files': [],
            'm3u8_files': [],
            'ts_files': [],
            'all_files': []
        }


def generate_presigned_url(file_key, expiration=3600):
    """
    Generate a presigned URL for an S3 file using regional endpoint

    Args:
        file_key (str): S3 object key (file path)
        expiration (int): URL expiration time in seconds (default: 1 hour)

    Returns:
        str: Presigned URL or None if failed
    """
    try:
        # Use regional endpoint to avoid redirects
        region = settings.AWS_S3_REGION_NAME
        bucket = settings.AWS_STORAGE_BUCKET_NAME

        # Create S3 client with explicit region endpoint
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=region,
            config=boto3.session.Config(
                signature_version='s3v4',
                s3={'addressing_style': 'virtual'}
            )
        )

        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': bucket,
                'Key': file_key
            },
            ExpiresIn=expiration
        )

        return url

    except ClientError as e:
        print(f"Error generating presigned URL: {e}")
        return None


def get_recording_playback_url(sid):
    """
    Get the playback URL for a recording (MP4 or M3U8)

    Prefers MP4 files over HLS for simpler playback.

    Args:
        sid (str): Session ID from recording

    Returns:
        dict: {
            'url': presigned URL,
            'type': 'mp4' or 'hls',
            'mime_type': MIME type for the file
        } or None if no files found
    """
    files = list_recording_files(sid)

    # Prefer MP4 files (simpler, no streaming required)
    if files['mp4_files']:
        # Get the first MP4 file (usually there's only one in mix mode)
        mp4_file = files['mp4_files'][0]
        url = generate_presigned_url(mp4_file, expiration=7200)  # 2 hours

        return {
            'url': url,
            'type': 'mp4',
            'mime_type': 'video/mp4'
        }

    # Fallback to HLS if MP4 not available
    if files['m3u8_files']:
        # Find the master M3U8 file (usually the shortest filename)
        master_m3u8 = min(files['m3u8_files'], key=len)
        url = generate_presigned_url(master_m3u8, expiration=7200)  # 2 hours

        return {
            'url': url,
            'type': 'hls',
            'mime_type': 'application/x-mpegURL'
        }

    return None


def setup_s3_cors():
    """
    Configure CORS on the S3 bucket to allow browser video playback

    This allows the browser to load video files from S3 without CORS errors.
    """
    try:
        s3_client = _get_s3_client()
        bucket = settings.AWS_STORAGE_BUCKET_NAME

        cors_configuration = {
            'CORSRules': [{
                'AllowedHeaders': ['*'],
                'AllowedMethods': ['GET', 'HEAD'],
                'AllowedOrigins': ['*'],  # Allow all origins (you can restrict this in production)
                'ExposeHeaders': ['ETag'],
                'MaxAgeSeconds': 3000
            }]
        }

        s3_client.put_bucket_cors(
            Bucket=bucket,
            CORSConfiguration=cors_configuration
        )

        print(f"✅ CORS configuration applied to bucket: {bucket}")
        return True

    except ClientError as e:
        print(f"❌ Error setting up CORS: {e}")
        return False
