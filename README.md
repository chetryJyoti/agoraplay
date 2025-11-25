# AgoraPlay

AgoraPlay is an open-source Django application that showcases seamless integration of Agora's real-time video, voice, and interactive communication features through modular, production-ready examples.

## What is this?

AgoraPlay demonstrates how to build real-time communication features with:
- **Django** backend with modular architecture
- **Agora SDK** for real-time video, audio, and messaging
- **Cloud Recording** with AWS S3 storage integration
- **RESTful APIs** for token generation and service management
- Production-ready code structure and best practices

## Quick Setup

1. **Install dependencies**
   ```bash
   pip install -r requrements.txt
   ```

2. **Get Agora credentials**
   - Sign up at https://console.agora.io/
   - Create a project and enable App Certificate
   - Copy your App ID and Certificate
   - For cloud recording: Enable Cloud Recording and get Customer ID & Certificate

3. **Configure AWS S3 (optional, for cloud recording)**
   - Create an S3 bucket in your AWS account
   - Get your AWS Access Key ID and Secret Access Key
   - Configure CORS for the bucket (run `python setup_s3_cors.py`)

4. **Configure environment**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your credentials:
   ```
   # Required for basic functionality
   AGORA_APP_ID=your_app_id
   AGORA_APP_CERTIFICATE=your_certificate

   # Required for cloud recording
   AGORA_CUSTOMER_ID=your_customer_id
   AGORA_CUSTOMER_CERTIFICATE=your_customer_certificate

   # Required for cloud recording storage
   AWS_ACCESS_KEY_ID=your_aws_access_key
   AWS_SECRET_ACCESS_KEY=your_aws_secret_key
   AWS_STORAGE_BUCKET_NAME=your_bucket_name
   AWS_S3_REGION_NAME=us-east-1
   ```

5. **Run the server**
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

6. **Try the demo**
   - Open http://localhost:8000/rtc/demo/
   - Enter a channel name and click "Join Call"
   - Open same URL in another tab to test video call
   - Click the record button to start cloud recording
   - View recordings at http://localhost:8000/rtc/recordings/

## Project Structure

```
agoraplay/
    core/              # Shared Agora utilities
        agora_utils.py    # Token generation & recording logic
        api_views.py      # API endpoints (token, recording)
        api_urls.py       # API routes
        models.py         # Recording database model

    rtc/               # Video call feature
        views.py          # Demo and recordings page views
        urls.py           # Web routes
        templates/
            demo.html         # Video call with recording controls
            recordings.html   # Recordings management UI

    setup_s3_cors.py   # S3 CORS configuration script
    diagnose_s3.py     # S3 troubleshooting script
    .env               # Your credentials
```

## API Usage

### Generate Token

```bash
GET /api/agora/token/?channel=demo
```

**Response:**
```json
{
  "appId": "your_app_id",
  "token": "generated_token",
  "channel": "demo",
  "uid": 0
}
```

**Use in your app:**
```javascript
const response = await fetch('/api/agora/token/?channel=my-room');
const { appId, token, channel, uid } = await response.json();

// Join Agora channel
const client = AgoraRTC.createClient({ mode: "rtc", codec: "vp8" });
await client.join(appId, channel, token, uid);
```

### Cloud Recording APIs

**Start Recording:**
```bash
POST /api/agora/recording/start/
Content-Type: application/json

{
  "channel": "demo",
  "uid": "999999"
}
```

**Stop Recording:**
```bash
POST /api/agora/recording/stop/
Content-Type: application/json

{
  "resource_id": "your_resource_id",
  "sid": "your_session_id",
  "channel": "demo",
  "uid": "999999"
}
```

**List Recordings:**
```bash
GET /api/agora/recording/list/
```

**Get Playback URL:**
```bash
GET /api/agora/recording/playback/{recording_id}/
```

## URLs

### Web Pages
- `/rtc/demo/` - Video call demo page with recording controls
- `/rtc/recordings/` - Recordings management and playback page

### API Endpoints
- `/api/agora/token/` - Token generation
- `/api/agora/recording/start/` - Start cloud recording
- `/api/agora/recording/stop/` - Stop cloud recording
- `/api/agora/recording/query/` - Query recording status
- `/api/agora/recording/list/` - List all recordings
- `/api/agora/recording/playback/{id}/` - Get recording playback URL

## Features

### Real-Time Video Communication
- HD video and audio streaming
- Multiple participants support
- Camera and microphone controls
- Participant count tracking
- Meeting duration timer

### Cloud Recording
- One-click recording from video call interface
- Automatic upload to AWS S3 bucket
- Support for MP4 and HLS formats
- Recording metadata stored in database
- Recordings management UI with search and playback
- Video.js player for HLS/MP4 playback
- Direct S3 access for file management

## How It Works

### Video Calls
1. User opens demo page and enters a channel name
2. Frontend requests a token from `/api/agora/token/`
3. Backend generates a secure token using Agora credentials
4. Frontend uses token to join Agora video channel
5. Real-time video streaming happens via Agora's network

### Cloud Recording
1. User clicks record button during a video call
2. Frontend calls `/api/agora/recording/start/` API
3. Backend acquires Agora cloud recording resource
4. Recording starts and files are uploaded to S3
5. User stops recording, files are finalized in S3
6. Recording metadata is saved to database
7. Users can view, search, and play recordings from the recordings page
