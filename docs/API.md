# AgoraPlay API Documentation

Complete API reference for AgoraPlay Agora services.

## Base URL

```
Development: http://localhost:8000
Production: https://your-domain.com
```

## Authentication

Currently, the API does not require authentication. For production use, consider adding:
- API keys
- JWT tokens
- OAuth 2.0

---

## Endpoints

### 1. Generate RTC Token

Generate a secure token for joining an Agora Real-Time Communication (RTC) channel.

#### Endpoint
```
GET /api/agora/token/
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `channel` | string | Yes | - | Channel name to join (e.g., "meeting-room-123") |
| `uid` | integer | No | 0 | User ID. Use 0 for dynamic assignment by Agora |

#### Request Examples

**cURL**
```bash
# Basic request
curl "http://localhost:8000/api/agora/token/?channel=demo"

# With custom UID
curl "http://localhost:8000/api/agora/token/?channel=meeting-room&uid=12345"
```

**JavaScript (Fetch API)**
```javascript
const response = await fetch('/api/agora/token/?channel=demo');
const data = await response.json();
console.log(data);
// { appId: "...", token: "006...", channel: "demo", uid: 0 }
```

**Python (requests)**
```python
import requests

response = requests.get(
    'http://localhost:8000/api/agora/token/',
    params={'channel': 'demo', 'uid': 12345}
)
token_data = response.json()
```

**Swift (iOS)**
```swift
let url = URL(string: "https://your-domain.com/api/agora/token/?channel=demo")!
let task = URLSession.shared.dataTask(with: url) { data, response, error in
    if let data = data {
        let tokenData = try? JSONDecoder().decode(TokenResponse.self, from: data)
        // Use tokenData.token, tokenData.appId, etc.
    }
}
task.resume()
```

**Kotlin (Android)**
```kotlin
val url = "https://your-domain.com/api/agora/token/?channel=demo"
val request = Request.Builder().url(url).build()

client.newCall(request).enqueue(object : Callback {
    override fun onResponse(call: Call, response: Response) {
        val tokenData = response.body?.string()
        // Parse JSON and use token
    }
})
```

#### Response

**Success (200 OK)**
```json
{
    "appId": "d3c7942d9ab94a12a4aff57f4876729a",
    "token": "006d3c7942d9ab94a12a4aff57f4876729aIAC...",
    "channel": "demo",
    "uid": 0
}
```

| Field | Type | Description |
|-------|------|-------------|
| `appId` | string | Agora Application ID |
| `token` | string | Time-limited RTC token (valid for 1 hour) |
| `channel` | string | Channel name that was requested |
| `uid` | integer | User ID (0 = dynamic assignment) |

**Error (400 Bad Request)**
```json
{
    "error": "channel parameter is required"
}
```

**Error (500 Internal Server Error)**
```json
{
    "error": "Agora credentials not configured"
}
```

#### Token Usage

Once you have the token, use it to join an Agora channel:

**Web (Agora Web SDK)**
```javascript
const client = AgoraRTC.createClient({ mode: "rtc", codec: "vp8" });

// Get token from API
const response = await fetch('/api/agora/token/?channel=demo');
const { appId, token, channel, uid } = await response.json();

// Join channel
await client.join(appId, channel, token, uid);

// Create and publish tracks
const audioTrack = await AgoraRTC.createMicrophoneAudioTrack();
const videoTrack = await AgoraRTC.createCameraVideoTrack();
await client.publish([audioTrack, videoTrack]);
```

**iOS (Agora iOS SDK)**
```swift
import AgoraRtcKit

let agoraKit = AgoraRtcEngineKit.sharedEngine(
    withAppId: tokenData.appId,
    delegate: self
)

agoraKit.joinChannel(
    byToken: tokenData.token,
    channelId: tokenData.channel,
    info: nil,
    uid: UInt(tokenData.uid)
) { (channel, uid, elapsed) in
    print("Join channel success")
}
```

**Android (Agora Android SDK)**
```kotlin
import io.agora.rtc2.RtcEngine

val mRtcEngine = RtcEngine.create(context, appId, null)

mRtcEngine.joinChannel(
    token,
    channel,
    null,
    uid
)
```

#### Token Lifecycle

- **Expiration**: Tokens expire after **1 hour** by default
- **Renewal**: Request a new token before expiration
- **Best Practice**: Refresh tokens at 90% of their lifetime (54 minutes)

```javascript
// Token refresh example
let tokenRefreshTimer;

function scheduleTokenRefresh() {
    // Refresh after 54 minutes (90% of 1 hour)
    tokenRefreshTimer = setTimeout(async () => {
        const response = await fetch('/api/agora/token/?channel=demo');
        const { token } = await response.json();

        // Renew token with Agora
        await client.renewToken(token);

        // Schedule next refresh
        scheduleTokenRefresh();
    }, 54 * 60 * 1000);
}
```

---

## Future Endpoints

The following endpoints are planned for future releases:

### 2. Generate RTM Token (Coming Soon)

Generate a token for Agora Real-Time Messaging (chat).

```
GET /api/agora/rtm/token/
```

**Parameters:**
- `userId` (required): User identifier for chat

### 3. Start Cloud Recording (Coming Soon)

Start recording a channel.

```
POST /api/agora/recording/start/
```

**Body:**
```json
{
    "channel": "demo",
    "uid": 0,
    "recordingConfig": {
        "maxIdleTime": 30,
        "streamTypes": 2
    }
}
```

### 4. Stop Cloud Recording (Coming Soon)

Stop an active recording.

```
POST /api/agora/recording/stop/
```

**Body:**
```json
{
    "resourceId": "...",
    "sid": "..."
}
```

---

## Rate Limiting

**Current**: No rate limiting implemented

**Recommended for Production**:
- 100 requests per minute per IP
- 1000 requests per hour per API key
- Implement using Django REST Framework throttling:

```python
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/minute',
        'user': '1000/hour'
    }
}
```

---

## Error Codes

| HTTP Code | Error | Description |
|-----------|-------|-------------|
| 200 | Success | Request successful |
| 400 | Bad Request | Missing or invalid parameters |
| 401 | Unauthorized | Authentication required (future) |
| 403 | Forbidden | Insufficient permissions (future) |
| 429 | Too Many Requests | Rate limit exceeded (future) |
| 500 | Internal Server Error | Server error or misconfiguration |

---

## CORS

Cross-Origin Resource Sharing (CORS) is enabled for all origins in development.

**Development**:
```python
CORS_ALLOW_ALL_ORIGINS = True
```

**Production (Recommended)**:
```python
CORS_ALLOWED_ORIGINS = [
    "https://yourdomain.com",
    "https://app.yourdomain.com",
    "https://mobile.yourdomain.com",
]
```

---

## Webhooks (Future)

Future support for Agora webhooks:

```
POST /api/agora/webhooks/rtc/
POST /api/agora/webhooks/recording/
```

These will receive events from Agora cloud:
- User joined/left channel
- Recording started/stopped
- Channel created/destroyed

---

## Testing

### Manual Testing

Use the interactive demo page:
```
http://localhost:8000/rtc/demo/
```

### API Testing with cURL

```bash
# Test token generation
curl -i "http://localhost:8000/api/agora/token/?channel=test"

# Test with UID
curl -i "http://localhost:8000/api/agora/token/?channel=test&uid=99999"

# Test error handling (missing channel)
curl -i "http://localhost:8000/api/agora/token/"
```

### Integration Testing

```python
# tests/test_api.py
from django.test import TestCase
from django.urls import reverse

class TokenAPITestCase(TestCase):
    def test_generate_token_success(self):
        response = self.client.get(
            reverse('agora_api:rtc_token'),
            {'channel': 'test'}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('appId', data)
        self.assertIn('token', data)

    def test_generate_token_missing_channel(self):
        response = self.client.get(reverse('agora_api:rtc_token'))
        self.assertEqual(response.status_code, 400)
```

---

## Support

- **GitHub Issues**: Report bugs and request features
- **Agora Docs**: https://docs.agora.io/
- **Agora Support**: https://www.agora.io/en/support/

---

## Changelog

### v1.0.0 (Current)
- Initial release
- RTC token generation endpoint
- Basic error handling
- CORS support

### Future Releases
- v1.1.0: RTM token generation
- v1.2.0: Cloud recording API
- v1.3.0: Authentication and rate limiting
- v2.0.0: Webhooks support
