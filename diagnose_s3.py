"""
Diagnostic script to troubleshoot S3 recording issues

This script will:
1. Check S3 bucket access and list all files
2. Verify AWS credentials
3. Check recent recordings in the database
4. Display file structure in S3
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agoraplay.settings')
django.setup()

import boto3
from django.conf import settings
from core.models import Recording
from botocore.exceptions import ClientError


def check_aws_credentials():
    """Verify AWS credentials are configured"""
    print("=" * 60)
    print("1. CHECKING AWS CREDENTIALS")
    print("=" * 60)

    print(f"AWS_ACCESS_KEY_ID: {'✓ Set' if settings.AWS_ACCESS_KEY_ID else '✗ Missing'}")
    print(f"AWS_SECRET_ACCESS_KEY: {'✓ Set' if settings.AWS_SECRET_ACCESS_KEY else '✗ Missing'}")
    print(f"AWS_STORAGE_BUCKET_NAME: {settings.AWS_STORAGE_BUCKET_NAME or '✗ Missing'}")
    print(f"AWS_S3_REGION_NAME: {settings.AWS_S3_REGION_NAME or '✗ Missing'}")
    print()


def check_s3_bucket_access():
    """Test S3 bucket access"""
    print("=" * 60)
    print("2. CHECKING S3 BUCKET ACCESS")
    print("=" * 60)

    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )

        bucket = settings.AWS_STORAGE_BUCKET_NAME

        # Try to list bucket
        response = s3_client.list_objects_v2(
            Bucket=bucket,
            MaxKeys=100
        )

        if 'Contents' in response:
            print(f"✓ Successfully connected to bucket: {bucket}")
            print(f"✓ Found {len(response['Contents'])} files in bucket")
            print()
            return s3_client, response['Contents']
        else:
            print(f"✓ Successfully connected to bucket: {bucket}")
            print(f"⚠ Bucket is empty (no files found)")
            print()
            return s3_client, []

    except ClientError as e:
        error_code = e.response['Error']['Code']
        print(f"✗ Failed to access S3 bucket: {error_code}")
        print(f"  Error: {e.response['Error']['Message']}")
        print()
        return None, []
    except Exception as e:
        print(f"✗ Unexpected error: {str(e)}")
        print()
        return None, []


def list_all_s3_files(s3_objects):
    """Display all files in S3 bucket"""
    print("=" * 60)
    print("3. ALL FILES IN S3 BUCKET")
    print("=" * 60)

    if not s3_objects:
        print("No files found in S3 bucket")
        print()
        return

    print(f"Total files: {len(s3_objects)}\n")

    # Group files by prefix
    file_groups = {}
    for obj in s3_objects:
        key = obj['Key']
        # Extract first part of path as prefix
        prefix = key.split('/')[0] if '/' in key else 'root'

        if prefix not in file_groups:
            file_groups[prefix] = []
        file_groups[prefix].append(key)

    # Display grouped files
    for prefix, files in sorted(file_groups.items()):
        print(f"\nPrefix: {prefix}/")
        print(f"  Files: {len(files)}")
        for file in sorted(files)[:10]:  # Show first 10 files
            size_kb = s3_objects[s3_objects.index(next(o for o in s3_objects if o['Key'] == file))]['Size'] / 1024
            print(f"    - {file} ({size_kb:.2f} KB)")
        if len(files) > 10:
            print(f"    ... and {len(files) - 10} more files")
    print()


def check_recent_recordings():
    """Check recent recordings in database"""
    print("=" * 60)
    print("4. RECENT RECORDINGS IN DATABASE")
    print("=" * 60)

    recordings = Recording.objects.all().order_by('-started_at')[:5]

    if not recordings:
        print("No recordings found in database")
        print()
        return []

    print(f"Total recordings: {Recording.objects.count()}")
    print(f"\nMost recent recordings:\n")

    for i, rec in enumerate(recordings, 1):
        print(f"{i}. Recording ID: {rec.id}")
        print(f"   Channel: {rec.channel_name}")
        print(f"   Status: {rec.status}")
        print(f"   SID: {rec.sid}")
        print(f"   Started: {rec.started_at}")
        print(f"   Stopped: {rec.stopped_at or 'Still recording'}")
        print(f"   S3 Bucket: {rec.s3_bucket}")
        print(f"   S3 File List: {rec.s3_file_list or 'Not available'}")
        print()

    return recordings


def check_sid_in_s3(recordings, s3_objects):
    """Check if recording SIDs match S3 file prefixes"""
    print("=" * 60)
    print("5. MATCHING RECORDINGS WITH S3 FILES")
    print("=" * 60)

    if not recordings:
        print("No recordings to check")
        print()
        return

    if not s3_objects:
        print("No S3 files to match against")
        print()
        return

    # Get all S3 prefixes
    s3_prefixes = set()
    for obj in s3_objects:
        key = obj['Key']
        prefix = key.split('/')[0] if '/' in key else key
        s3_prefixes.add(prefix)

    print(f"S3 prefixes found: {len(s3_prefixes)}\n")

    for rec in recordings:
        sid = rec.sid
        # Check if SID exists as prefix in S3
        matching_files = [obj['Key'] for obj in s3_objects if obj['Key'].startswith(sid)]

        if matching_files:
            print(f"✓ Recording {rec.id} (SID: {sid})")
            print(f"  Found {len(matching_files)} files in S3")
            for file in matching_files[:5]:
                print(f"    - {file}")
            if len(matching_files) > 5:
                print(f"    ... and {len(matching_files) - 5} more")
        else:
            print(f"✗ Recording {rec.id} (SID: {sid})")
            print(f"  No files found in S3 with this SID prefix")
        print()


def suggest_solutions():
    """Provide troubleshooting suggestions"""
    print("=" * 60)
    print("6. TROUBLESHOOTING SUGGESTIONS")
    print("=" * 60)
    print("""
If no files are found in S3:

1. VERIFY AGORA HAS S3 PERMISSIONS:
   - In AWS IAM, ensure Agora has permission to upload to your bucket
   - Check S3 bucket policy allows writes from Agora
   - Agora needs: s3:PutObject, s3:PutObjectAcl permissions

2. CHECK RECORDING CONFIGURATION:
   - Verify storageConfig is correctly passed to Agora API
   - Check AWS credentials in .env file are correct
   - Ensure bucket name and region match your AWS setup

3. WAIT FOR UPLOAD TO COMPLETE:
   - Agora uploads files AFTER recording stops
   - Upload can take several minutes depending on file size
   - Check Agora dashboard for upload status

4. VERIFY BUCKET REGION:
   - Check AWS_S3_REGION_NAME matches your bucket's actual region
   - Region codes must match Agora's expected format

5. CHECK AGORA CUSTOMER CREDENTIALS:
   - Verify AGORA_CUSTOMER_ID and AGORA_CUSTOMER_CERTIFICATE
   - These are different from APP_ID and APP_CERTIFICATE

6. REVIEW STOP RESPONSE:
   - The serverResponse.fileList contains upload details
   - Check if files are listed in the stop recording response
""")


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("AGORA CLOUD RECORDING S3 DIAGNOSTICS")
    print("=" * 60 + "\n")

    # Run all checks
    check_aws_credentials()
    s3_client, s3_objects = check_s3_bucket_access()
    list_all_s3_files(s3_objects)
    recordings = check_recent_recordings()
    check_sid_in_s3(recordings, s3_objects)
    suggest_solutions()

    print("=" * 60)
    print("DIAGNOSTICS COMPLETE")
    print("=" * 60 + "\n")
