# AgoraPlay

AgoraPlay is an open-source Django application that showcases seamless integration of Agora's real-time video, voice, and interactive communication features through modular, production-ready examples.

## What is this?

AgoraPlay demonstrates how to build real-time communication features with:
- **Django** backend with modular architecture
- **Agora SDK** for real-time video, audio, and messaging
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

3. **Configure environment**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your Agora credentials:
   ```
   AGORA_APP_ID=your_app_id
   AGORA_APP_CERTIFICATE=your_certificate
   ```

4. **Run the server**
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

5. **Try the demo**
   - Open http://localhost:8000/rtc/demo/
   - Enter a channel name and click "Join Call"
   - Open same URL in another tab to test video call

## Project Structure

```
agoraplay/
    core/              # Shared Agora utilities
        agora_utils.py    # Token generation logic
        api_views.py      # API endpoints
        api_urls.py       # API routes

    rtc/               # Video call feature
        views.py          # Demo page view
        urls.py           # Web routes
        templates/        # Demo HTML
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

## URLs

- `/rtc/demo/` - Video call demo page
- `/api/agora/token/` - Token generation API

## How It Works

1. User opens demo page and enters a channel name
2. Frontend requests a token from `/api/agora/token/`
3. Backend generates a secure token using Agora credentials
4. Frontend uses token to join Agora video channel
5. Real-time video streaming happens via Agora's network

## Next Steps

Want to add more features? You can:
- Add mute/unmute buttons
- Support multiple remote users
- Add text chat (Agora RTM)
- Record calls (Agora Cloud Recording)

## License

MIT
