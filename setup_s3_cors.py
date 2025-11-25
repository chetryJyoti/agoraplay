#!/usr/bin/env python
"""
Setup S3 CORS Configuration

This script configures CORS on your S3 bucket to allow browser video playback.
Run this once after setting up your recording system.

Usage:
    python setup_s3_cors.py
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agoraplay.settings')
django.setup()

from core.agora_utils import setup_s3_cors

if __name__ == '__main__':
    print("🔧 Setting up S3 CORS configuration...")
    print("=" * 50)

    success = setup_s3_cors()

    if success:
        print("\n✅ SUCCESS! Your S3 bucket is now configured for browser video playback.")
        print("\nYou can now play recordings directly in the browser!")
    else:
        print("\n❌ Failed to configure CORS.")
        print("\nManual setup instructions:")
        print("1. Go to AWS S3 Console")
        print("2. Select your bucket: agora-recordings-test1")
        print("3. Go to 'Permissions' tab")
        print("4. Scroll to 'Cross-origin resource sharing (CORS)'")
        print("5. Click 'Edit' and paste this configuration:")
        print("""
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "HEAD"],
        "AllowedOrigins": ["*"],
        "ExposeHeaders": ["ETag"],
        "MaxAgeSeconds": 3000
    }
]
        """)
        print("6. Click 'Save changes'")
