# CLAUDE.md - Development Context & Architecture

> This document provides comprehensive technical context for AI assistants (Claude) working on the Sobub AI codebase. It covers architecture, design decisions, component relationships, and development guidelines.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Component Deep Dive](#component-deep-dive)
4. [Key Technical Decisions](#key-technical-decisions)
5. [Data Flow](#data-flow)
6. [File Structure Guide](#file-structure-guide)
7. [Development Notes](#development-notes)
8. [Common Patterns](#common-patterns)
9. [Future Enhancements](#future-enhancements)
10. [Troubleshooting Guide](#troubleshooting-guide)

---

## Project Overview

**Sobub AI** (Silence Occasionally Broken Up By AI) is a context-aware ambient audio companion that listens to conversations, analyzes context, and randomly plays relevant meme audio clips.

### Core Concept

The system operates as a "background companion" that:
- Continuously listens to ambient conversation via microphone (HTTPS required for mobile)
- Transcribes speech in near real-time using faster-whisper (optimized Whisper implementation)
- Analyzes transcriptions for contextual matches against user-defined tags
- Randomly triggers playback of relevant audio memes based on probability and cooldown settings
- Microphone pauses automatically during audio playback to prevent feedback
- Cooldown starts AFTER audio finishes playing (not when triggered)
- Runs 100% locally with GPU acceleration (no external API calls)

### Design Philosophy

1. **Privacy First**: All processing happens locally on the user's machine
2. **Non-Intrusive**: Designed to blend into the background with random, spaced-out triggers
3. **Context-Aware**: Matches conversation topics to audio content via flexible tagging system
4. **Mobile-Friendly**: Optimized for phone control while running on a PC
5. **GPU-Optimized**: Leverages NVIDIA GPUs for fast Whisper inference

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         USER DEVICES                         │
├─────────────────────────────────────────────────────────────┤
│   PC Browser (https://localhost)  │  Mobile (https://PC_IP)  │
└─────────────────┬───────────────────────────┬───────────────┘
                  │                           │
                  ├───────────────────────────┘
                  │          HTTPS (443)
                  ▼
         ┌────────────────────────┐
         │   Nginx Reverse Proxy  │  (Port 443/80)
         │   - SSL termination    │
         │   - Auto cert gen      │
         │   - Request routing    │
         └────────┬───────────────┘
                  │
          ┌───────┴────────┐
          │                │
          ▼                ▼
   ┌────────────────┐   ┌──────────────────────┐
   │  Frontend      │   │  Backend             │
   │  (Port 5173)   │   │  (Port 8000)         │
   │  - Vite 7      │   │  - FastAPI           │
   │  - React 18    │   │  - faster-whisper    │
   │  - Node 20     │   │  - CUDA 12.3 + cuDNN │
   └────────────────┘   └──────────┬───────────┘
                                   │
                    ┌──────────────┴──────────┐
                    │                         │
              REST API                    WebSocket
                    │                         │
                    ▼                         ▼
    ┌─────────────────────────────────────────────┐
    │         FastAPI Backend Services            │
    │  ┌─────────────────────┐    │
    │  │  WebSocket Handler  │    │
    │  │  - Audio streaming  │    │
    │  │  - Real-time comms  │    │
    │  └──────────┬──────────┘    │
    │             │                │
    │  ┌──────────▼──────────┐    │
    │  │  Whisper Service    │    │
    │  │  - GPU inference    │    │
    │  │  - Model: base      │    │
    │  └──────────┬──────────┘    │
    │             │                │
    │  ┌──────────▼──────────┐    │
    │  │  Context Analyzer   │    │
    │  │  - Tag matching     │    │
    │  │  - Keyword search   │    │
    │  └──────────┬──────────┘    │
    │             │                │
    │  ┌──────────▼──────────┐    │
    │  │  Trigger Engine     │    │
    │  │  - Cooldown logic   │    │
    │  │  - Probability RNG  │    │
    │  │  - Random selection │    │
    │  └──────────┬──────────┘    │
    │             │                │
    │  ┌──────────▼──────────┐    │
    │  │   Meme Manager      │    │
    │  │  - File storage     │    │
    │  │  - Metadata         │    │
    │  └──────────┬──────────┘    │
    │             │                │
    │  ┌──────────▼──────────┐    │
    │  │   SQLite Database   │    │
    │  │  - Memes table      │    │
    │  │  - Settings table   │    │
    │  └─────────────────────┘    │
    └─────────────────────────────┘
```

### Technology Stack

**Backend:**
- Python 3.10
- FastAPI (web framework)
- Uvicorn (ASGI server)
- faster-whisper (optimized Whisper implementation for speech recognition)
- PyTorch 2.1+ (ML framework)
- CUDA 12.3.2 + cuDNN 9 (GPU acceleration)
- SQLite (database via aiosqlite)
- WebSockets (real-time communication)

**Frontend:**
- React 18
- Vite 7 (build tool)
- Node.js 20
- TailwindCSS (styling)
- React Router (navigation)
- Native WebSocket API
- Native Fetch API

**Infrastructure:**
- Docker + Docker Compose
- NVIDIA Container Toolkit
- Nginx reverse proxy (HTTPS with auto-generated self-signed certificates)
- Bridge networking

---

## Component Deep Dive

### Backend Components

#### 1. Main Application (`backend/app/main.py`)

**Purpose**: FastAPI application entry point, API routes, and server configuration.

**Key Responsibilities:**
- Define REST API endpoints for CRUD operations
- Configure CORS middleware (allows all origins for development)
- Set up static file serving for audio files
- Initialize database on startup
- Configure Uvicorn server with 0.0.0.0 binding (allows external connections)

**Important Routes:**
- `GET /api/memes` - List all meme audio files
- `POST /api/memes` - Upload new audio file with tags
- `PUT /api/memes/{id}` - Update tags for existing meme
- `DELETE /api/memes/{id}` - Delete meme
- `GET /api/memes/{id}/audio` - Stream audio file
- `GET /api/settings` - Get current settings
- `PUT /api/settings` - Update settings
- `GET /api/status` - System status check
- `GET /api/tags` - Get all unique tags

**CORS Configuration:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Development: allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Note**: For production, restrict `allow_origins` to specific domains.

---

#### 2. WebSocket Handler (`backend/app/websocket.py`)

**Purpose**: Real-time bidirectional communication for audio streaming and transcriptions.

**Architecture:**
- Each client gets a unique connection identified by `client_id`
- Receives binary audio chunks from browser MediaRecorder (WebM/Opus format)
- Sends JSON messages for transcriptions and triggers
- Maintains connection state per client

**Message Flow:**

```
Client → Server (Binary):
  ┌──────────────────────┐
  │ Audio Chunk (WebM)   │
  │ 3-second segments    │
  └──────────────────────┘

Server → Client (JSON):
  {
    "type": "transcription",
    "text": "recognized text",
    "timestamp": 1234567890
  }

  {
    "type": "trigger",
    "meme_id": 42,
    "meme_name": "example.mp3",
    "transcription": "text that triggered",
    "matched_tags": ["tag1", "tag2"]
  }
```

**Audio Processing Pipeline:**
1. Receive WebM audio chunk (binary)
2. Save to temporary file
3. Convert to format Whisper expects (done by Whisper automatically)
4. Send to Whisper service for transcription
5. Send transcription to context analyzer
6. If match found, consult trigger engine
7. If triggered, send trigger message to client
8. Clean up temporary files

**Connection Management:**
- Client connects: `ws://HOST:8000/ws/{client_id}`
- Server maintains client-specific state
- Automatic cleanup on disconnect
- Error handling for dropped connections

---

#### 3. Whisper Service (`backend/app/whisper_service.py`)

**Purpose**: Speech-to-text transcription using faster-whisper (optimized Whisper implementation).

**Model Configuration:**
- Default: Whisper "base" model (74M parameters)
- Configurable via Settings UI (tiny, base, small, medium, large)
- Trade-off: smaller = faster but less accurate, larger = slower but more accurate
- Multi-language support: en, pt, es, fr, de, and 90+ others

**GPU Acceleration:**
- Automatically detects CUDA availability
- Falls back to CPU if GPU unavailable
- Uses CTranslate2 for optimized inference (2-4x faster than openai-whisper)
- Uses FP16 on GPU for additional 2x speed boost
- Typical inference time: 0.5-2 seconds per 3-second chunk (base model on RTX 4070)

**Audio Processing:**
- Accepts WebM/Opus audio from browser MediaRecorder
- Saves to temporary file for processing
- ffmpeg (via faster-whisper) decodes WebM automatically
- Skips chunks < 1KB (incomplete data)
- Automatic cleanup of temporary files

**Key Methods:**
- `transcribe_audio(audio_data: bytes, language: str) → str`: Main transcription function
- Returns cleaned text (lowercase, stripped)

**Performance Notes:**
- First transcription is slow (model loading ~5-10s)
- Subsequent transcriptions are fast (model cached in GPU memory)
- Memory usage: ~1-2GB GPU RAM for base model
- Model downloaded once to `/app/models/` (persisted via Docker volume)
- faster-whisper is 2-4x faster than openai-whisper with same accuracy

---

#### 4. Context Analyzer (`backend/app/context_analyzer.py`)

**Purpose**: Match transcribed text against meme tags to find relevant audio.

**Matching Algorithm:**

```python
def find_matches(transcription: str, memes: List[Meme]) → List[Meme]:
    matches = []
    transcription_lower = transcription.lower()

    for meme in memes:
        for tag in meme.tags:
            if tag.lower() in transcription_lower:
                matches.append(meme)
                break  # Count meme only once

    return matches
```

**Matching Strategy:**
- Simple substring matching (case-insensitive)
- Tag "football" matches "I love football" and "footballer"
- Each meme matches at most once per transcription
- No fuzzy matching (intentionally simple)

**Example:**
```
Transcription: "That goal was incredible!"
Meme Tags: ["goal", "football", "sports"]
Result: MATCH (contains "goal")

Transcription: "Let's cook dinner"
Meme Tags: ["chef", "cooking", "recipe"]
Result: MATCH (contains "cooking" via "cook")
```

**Future Enhancement Ideas:**
- Semantic matching using embeddings
- Fuzzy matching for typos/variations
- Multi-word phrase matching
- Weighted tag importance

---

#### 5. Trigger Engine (`backend/app/trigger_engine.py`)

**Purpose**: Decide whether to play audio based on cooldown and probability.

**Logic Flow:**

```python
def attempt_trigger(matching_memes: List[Dict]) → Optional[Dict]:
    # 1. Check cooldown
    if is_cooldown_active():
        return None  # Still in cooldown

    # 2. Check probability
    roll = random.uniform(0, 100)
    if roll >= trigger_probability:
        return None  # Probability check failed

    # 3. Select random meme
    selected = random.choice(matching_memes)

    # Note: Cooldown is NOT started here!
    # It starts when audio finishes playing (via audio_ended control message)
    return selected
```

**Cooldown Mechanism:**
- Tracks timestamp of last trigger
- Prevents trigger spam
- Configurable per session (default: 180 seconds / 3 minutes)
- **Critical**: Cooldown starts AFTER audio finishes playing, not when triggered
- This ensures cooldown is based on when audio ends, not when it starts
- Frontend sends `audio_ended` control message to start cooldown

**Cooldown Timing Flow:**
```
1. Tag match found → attempt_trigger()
2. Probability passes → meme selected
3. Trigger message sent to client
4. Client plays audio
5. Audio finishes → client sends "audio_ended" message
6. Backend receives "audio_ended" → start_cooldown()
7. Cooldown timer starts NOW
```

**Probability System:**
- User sets percentage (0-100)
- Default: 50% = 50% chance to trigger (if cooldown passed)
- Adds randomness/unpredictability
- Makes system feel more "organic"

**Random Selection:**
```python
def select_random_meme(matches: List[Meme]) → Meme:
    return random.choice(matches)
```

**Example Scenario:**
```
Settings: cooldown=180s (3min), probability=50%
Last audio ended: 4 minutes ago
Matches found: 3 memes

Flow:
1. 4min > 3min → cooldown passed ✓
2. random.uniform(0, 100) = 42 → 42 < 50 → probability passed ✓
3. random.choice([meme1, meme2, meme3]) → meme2
4. Send trigger to client (cooldown NOT started yet)
5. Client plays audio
6. Audio finishes (10 seconds later)
7. Client sends "audio_ended" message
8. Backend starts cooldown NOW ✓
```

---

#### 6. Meme Manager (`backend/app/meme_manager.py`)

**Purpose**: Handle file storage and retrieval of audio files.

**File Operations:**
- Upload: Save MP3 to `/app/data/audio_files/{id}.mp3`
- Retrieve: Read file and stream to client
- Delete: Remove file from filesystem
- List: Query all files from database

**Storage Structure:**
```
/app/data/
├── memes.db              # SQLite database
└── audio_files/
    ├── 1.mp3
    ├── 2.mp3
    └── 3.mp3
```

**Validation:**
- File type: Must be audio/mpeg (MP3)
- File size: No explicit limit (trust user)
- Filename: Stored as original filename in DB, saved as `{id}.mp3` on disk

---

#### 7. Database (`backend/app/database.py`)

**Purpose**: SQLite operations for persistence.

**Schema:**

```sql
CREATE TABLE memes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    tags TEXT NOT NULL,  -- Comma-separated string
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    play_count INTEGER DEFAULT 0  -- Track how many times played
);

CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Default settings (key-value pairs):
-- cooldown_seconds: '180' (3 minutes)
-- trigger_probability: '50' (50%)
-- whisper_model: 'base'
-- chunk_length_seconds: '3'
-- language: 'pt' (Portuguese)
```

**Tag Storage:**
- Stored as comma-separated string: `"football, goal, sports"`
- Parsed to list in Python: `["football", "goal", "sports"]`
- Alternative approach: separate tags table with many-to-many relationship (not implemented)

**Async Operations:**
- Uses `aiosqlite` for async SQLite
- Prevents blocking the event loop
- Important for FastAPI async routes

---

#### 8. Models (`backend/app/models.py`)

**Purpose**: Pydantic models for data validation and serialization.

**Key Models:**

```python
class Meme(BaseModel):
    id: int
    filename: str
    tags: List[str]
    created_at: str
    play_count: int

class SettingsResponse(BaseModel):
    cooldown_seconds: int
    trigger_probability: float  # 0-100
    whisper_model: str
    chunk_length_seconds: int
    language: str

class SettingsUpdate(BaseModel):
    cooldown_seconds: Optional[int] = None
    trigger_probability: Optional[float] = None
    chunk_length_seconds: Optional[int] = None
    language: Optional[str] = None
    whisper_model: Optional[str] = None
```

**Benefits:**
- Automatic request/response validation
- Type safety
- API documentation (OpenAPI/Swagger)
- Serialization/deserialization

---

#### 9. Nginx Reverse Proxy (`nginx/`)

**Purpose**: HTTPS reverse proxy with automatic SSL certificate generation.

**Key Features:**
- **SSL Termination**: Handles HTTPS encryption/decryption
- **Auto Certificate Generation**: Self-signed certs generated on first startup
- **Request Routing**: Routes requests to frontend/backend based on path
- **HTTP → HTTPS Redirect**: All HTTP traffic redirected to HTTPS

**Architecture:**
```
Browser (HTTPS) → Nginx (443) → Frontend (5173) / Backend (8000)
                                ↓
                         Self-signed SSL cert
```

**Request Routing:**
- `/` → Frontend React app (port 5173)
- `/api/*` → Backend FastAPI (port 8000)
- `/ws/*` → Backend WebSocket (port 8000)
- `/audio/*` → Backend audio files (port 8000)

**Auto Certificate Generation:**
- Entrypoint script checks for existing certificates
- If missing, generates self-signed cert for localhost + local IP
- Certificates stored in Docker volume (persists across rebuilds)
- Valid for 365 days

**Why HTTPS?**
- Mobile browsers require secure context for microphone access
- `navigator.mediaDevices.getUserMedia()` only works on HTTPS or localhost
- Without HTTPS, mobile users cannot use the microphone

**Configuration Files:**
- `nginx/conf/nginx.conf` - Nginx configuration
- `nginx/Dockerfile` - Container with auto-cert generation
- `nginx/docker-entrypoint.sh` - Auto-generates certs on startup
- `nginx/ssl/generate-certs.sh` - Manual cert generation script

---

### Frontend Components

#### 1. Main App (`frontend/src/App.jsx`)

**Purpose**: Root component, routing, and layout.

**Structure:**
```jsx
<Router>
  <Routes>
    <Route path="/" element={<SessionControl />} />
    <Route path="/settings" element={<Settings />} />
    <Route path="/library" element={<MemeLibrary />} />
  </Routes>
  <AudioPlayer />  {/* Global audio player */}
</Router>
```

**Global State:**
- Audio player state (managed by AudioPlayer component)
- WebSocket connection (managed by SessionControl)
- Settings (fetched from API)

---

#### 2. Session Control (`frontend/src/components/SessionControl.jsx`)

**Purpose**: Main control panel - start/stop sessions, view event log.

**State Management:**
```javascript
const [isActive, setIsActive] = useState(false);
const [isConnecting, setIsConnecting] = useState(false);
const [error, setError] = useState(null);
const [status, setStatus] = useState(null);
const [events, setEvents] = useState([]);  // Event log with all activity
const [showEventLog, setShowEventLog] = useState(true);  // Persisted to localStorage
```

**Event Log System:**
- Tracks all activity: transcriptions, matches, triggers, debug info, errors
- Each event has: type, timestamp, and type-specific data
- Limited to last 20 events (auto-truncates)
- Toggle visibility with switch component (saved to localStorage)
- Auto-scrolls to latest event

**Event Types:**
- `transcription`: Microphone captured and transcribed text
- `match`: Tags matched in transcription
- `trigger`: Meme audio triggered and playing
- `debug`: System info (cooldown, probability checks)
- `error`: Error messages

**WebSocket Integration:**
- Connects to backend on session start
- Listens for: transcriptions, matches, triggers, debug, errors
- Displays real-time event feed
- Triggers audio playback
- Sends `audio_ended` control message when audio finishes

**User Flow:**
1. Click "Start Session"
2. Request microphone permission (HTTPS required!)
3. Connect to WebSocket
4. Start recording (configurable chunk length, default 3s)
5. Display events as they arrive in real-time
6. Toggle event log visibility with switch
7. Click "Stop Session" to end (or navigate away - cleanup automatic)

---

#### 3. Audio Player (`frontend/src/components/AudioPlayer.jsx`)

**Purpose**: Global audio playback component with microphone pause integration.

**Features:**
- Plays triggered meme audio
- Notifies parent when playback starts/ends
- Triggers microphone pause during playback (prevents feedback)
- Sends `audio_ended` message to backend (starts cooldown)

**Implementation:**
```jsx
const audioRef = useRef(null);

useEffect(() => {
  if (triggerData) {
    playAudio(triggerData.meme_id);
  }
}, [triggerData]);

const handlePlay = () => {
  // Notify parent that audio started (pauses microphone)
  if (onPlayStart) onPlayStart();
};

const handleEnded = () => {
  // Notify parent that audio ended (resumes microphone)
  if (onPlayEnd) onPlayEnd();

  // Also notify about completion
  if (onPlayComplete) onPlayComplete();
};

// Event listeners on audio element
<audio
  ref={audioRef}
  onPlay={handlePlay}
  onEnded={handleEnded}
  onPause={handlePause}
  className="hidden"
/>
```

**Microphone Pause Flow:**
1. Trigger received → Audio starts playing
2. `onPlay` fires → Call `onPlayStart()` → Notify App.jsx
3. App.jsx calls `websocketService.setAudioPlaying(true)`
4. WebSocket service stops sending audio chunks
5. Audio finishes → `onEnded` fires → Call `onPlayEnd()`
6. App.jsx calls `websocketService.setAudioPlaying(false)` (resumes mic)
7. App.jsx sends `audio_ended` control message → Backend starts cooldown

---

#### 4. Settings (`frontend/src/components/Settings.jsx`)

**Purpose**: Configure cooldown and trigger probability.

**Form Controls:**
- Cooldown: Number input (minutes)
- Probability: Slider (0-100%)
- Visual feedback on save

**API Integration:**
```javascript
const saveSettings = async () => {
  const response = await api.updateSettings({
    cooldown_minutes: cooldown,
    trigger_probability: probability
  });
  // Show success message
};
```

---

#### 5. Meme Library (`frontend/src/components/MemeLibrary.jsx`)

**Purpose**: Upload, edit, and manage audio files.

**Features:**
- Upload MP3 files with tags
- Edit tags for existing memes
- Delete memes
- Play memes to preview
- Search/filter by tags

**Upload Flow:**
```javascript
const handleUpload = async (file, tags) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('tags', tags.join(', '));

  await api.createMeme(formData);
  refreshMemes();
};
```

---

#### 6. API Service (`frontend/src/services/api.js`)

**Purpose**: REST API client for backend communication.

**URL Detection with Nginx:**
```javascript
const getApiUrl = () => {
  if (typeof window !== 'undefined') {
    const protocol = window.location.protocol;
    const hostname = window.location.hostname;
    // With nginx reverse proxy, API is at same origin
    return `${protocol}//${hostname}`;
  }
  return 'http://localhost';
};
```

**How It Works with Nginx:**
- All requests go through nginx reverse proxy
- Nginx routes `/api/*` to backend:8000
- Frontend doesn't need to know backend port
- Works seamlessly on both PC and mobile
- Example: `https://localhost/api/memes` → nginx → `http://backend:8000/api/memes`

---

#### 7. WebSocket Service (`frontend/src/services/websocket.js`)

**Purpose**: WebSocket client for real-time communication and audio recording.

**Connection Management:**
```javascript
connect() {
  this.ws = new WebSocket(`${WS_URL}/ws/${this.clientId}`);

  this.ws.onopen = () => { /* Connected */ };
  this.ws.onmessage = (event) => { /* Handle message */ };
  this.ws.onerror = (error) => { /* Handle error */ };
  this.ws.onclose = () => { /* Disconnected */ };
}
```

**Audio Recording with Microphone Pause:**
```javascript
const stream = await navigator.mediaDevices.getUserMedia({
  audio: {
    sampleRate: 16000,
    channelCount: 1,
    echoCancellation: true,
    noiseSuppression: true,
    suppressLocalAudioPlayback: true,  // Prevent echo from speakers
  }
});

const mediaRecorder = new MediaRecorder(stream, {
  mimeType: 'audio/webm;codecs=opus'
});

// IMPORTANT: onstop must be async for proper sequencing
mediaRecorder.onstop = async () => {
  if (chunks.length > 0 && this.ws && this.ws.readyState === WebSocket.OPEN) {
    const blob = new Blob(chunks, { type: 'audio/webm' });

    // Check if audio is playing before sending
    if (!this.isAudioPlaying) {
      const buffer = await blob.arrayBuffer();
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(buffer);
      }
    } else {
      console.log('Skipping chunk send - meme audio is playing');
    }
  }

  // Start next recording cycle with small delay to prevent overlap
  if (this.isRecording) {
    setTimeout(() => this.startRecordingCycle(), 100);
  }
};

mediaRecorder.start(chunkLength * 1000); // Configurable chunk length
```

**Microphone Pause Feature:**
```javascript
setAudioPlaying(isPlaying) {
  this.isAudioPlaying = isPlaying;
  console.log(`Audio playback state: ${isPlaying ? 'playing' : 'stopped'}`);
}

// Called from App.jsx when audio starts/ends
// Prevents microphone from capturing meme audio playback
```

**Control Messages:**
```javascript
sendControlMessage(data) {
  if (this.ws && this.ws.readyState === WebSocket.OPEN) {
    this.ws.send(JSON.stringify(data));
  }
}

// Example: Notify backend that audio finished playing
sendControlMessage({ type: 'audio_ended' });
```

**Why Configurable Chunk Length?**
- Default 3 seconds: Balance between latency and context
- Longer chunks (5-10s): More context but higher latency
- Shorter chunks (1-2s): Lower latency but less context
- User can adjust in Settings based on preference

---

## Key Technical Decisions

### 1. Runtime URL Detection (Critical)

**Problem**: How to enable mobile devices to connect to PC backend without manual configuration?

**Solution**: Use `window.location.hostname` to dynamically construct backend URLs.

**Why This Works:**
- PC accesses frontend at `localhost:5173`
- Mobile accesses frontend at `192.168.1.100:5173`
- Frontend JavaScript sees different `window.location.hostname` values
- Backend URL is constructed as `${hostname}:8000`
- Mobile automatically connects to `192.168.1.100:8000` (the PC)

**Alternative Approaches Considered:**
- ❌ Environment variables: Requires rebuild on IP change
- ❌ Hardcoded IP: Fragile, network-dependent
- ❌ Configuration file: Extra user setup step
- ✅ Runtime detection: Zero config, works everywhere

**Code Location:**
- `frontend/src/services/api.js:3-13`
- `frontend/src/services/websocket.js:3-14`

---

### 2. Docker Compose Networking

**Decision**: Use bridge network with port mapping instead of host network.

**Rationale:**
- **Isolation**: Containers isolated from host processes
- **Portability**: Works on any Docker host
- **Flexibility**: Easy to add reverse proxy later
- **Development**: Matches production patterns

**Configuration:**
```yaml
networks:
  sobub-network:
    driver: bridge

services:
  backend:
    ports:
      - "8000:8000"
  frontend:
    ports:
      - "5173:5173"
```

**Trade-offs:**
- ✅ More portable and production-ready
- ✅ Better isolation and security
- ❌ Slightly more complex than `network_mode: host`
- ❌ Extra NAT layer (negligible performance impact)

---

### 3. Whisper Model Selection

**Decision**: Default to "base" model with configurable override.

**Rationale:**
- **Balance**: Good accuracy vs speed trade-off
- **GPU Fit**: Fits comfortably in 8GB VRAM
- **Fast**: 0.5-2s inference on RTX 4070
- **Accurate**: ~97% accuracy for clear English speech

**Model Comparison:**
| Model  | Parameters | GPU RAM | Speed (RTX 4070) | Accuracy |
|--------|-----------|---------|------------------|----------|
| tiny   | 39M       | ~1GB    | 0.2-0.5s        | ~90%     |
| base   | 74M       | ~1.5GB  | 0.5-2s          | ~97%     |
| small  | 244M      | ~2.5GB  | 1-4s            | ~98%     |
| medium | 769M      | ~5GB    | 3-10s           | ~99%     |
| large  | 1550M     | ~10GB   | 8-20s           | ~99.5%   |

**Configuration:**
```yaml
environment:
  - WHISPER_MODEL=base  # Can change to tiny, small, medium, large
```

---

### 4. WebSocket vs Server-Sent Events

**Decision**: WebSocket for bidirectional real-time communication.

**Why WebSocket?**
- Bidirectional: Client sends audio, server sends transcriptions
- Low latency: Persistent connection, no reconnection overhead
- Binary support: Can send audio chunks efficiently
- Standard: Well-supported by browsers

**Why Not SSE?**
- Unidirectional: Only server → client
- No binary: Would need Base64 encoding for audio
- More requests: Separate endpoint for audio upload

---

### 5. SQLite vs PostgreSQL

**Decision**: SQLite for simplicity and local-first design.

**Rationale:**
- **Simple**: Single file, no separate database server
- **Fast**: More than sufficient for single-user workload
- **Portable**: Database file can be backed up easily
- **Local-First**: Matches project philosophy

**When to Consider PostgreSQL:**
- Multi-user support
- Remote database access
- Complex queries with joins
- High concurrency (100+ writes/sec)

**Current Workload:**
- ~1 write/minute (new transcription + maybe trigger)
- ~10-100 memes total
- Single user
- SQLite is perfect for this

---

### 6. Frontend Build Tool: Vite vs Create React App

**Decision**: Vite for speed and modern defaults.

**Why Vite?**
- **Fast**: <1s dev server startup (vs 10-30s for CRA)
- **Modern**: ES modules, native ESM dev
- **Minimal**: Less boilerplate than CRA
- **Maintained**: Active development, CRA is deprecated

---

### 7. Styling: TailwindCSS vs CSS Modules

**Decision**: TailwindCSS for rapid development.

**Why Tailwind?**
- **Fast**: Utility-first, no context switching
- **Consistent**: Design system built-in
- **Mobile**: Responsive utilities (sm:, md:, lg:)
- **Dark Mode**: Built-in dark mode support

**Example:**
```jsx
<button className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
  Click me
</button>
```

---

## Data Flow

### End-to-End Flow: From Speech to Audio Playback

```
1. User speaks into microphone
   ↓
2. Browser MediaRecorder captures audio (3s chunks, WebM format)
   ↓
3. WebSocket sends binary audio chunk to backend
   ↓
4. Backend saves chunk to temp file
   ↓
5. Whisper Service transcribes audio (GPU)
   ↓
6. Context Analyzer checks transcription against all meme tags
   ↓
7. If matches found:
   ├─ Trigger Engine checks cooldown
   ├─ Trigger Engine checks probability
   └─ If both pass:
      ├─ Select random meme from matches
      └─ Send trigger message to client
   ↓
8. Frontend receives trigger message
   ↓
9. Frontend requests audio file via GET /api/memes/{id}/audio
   ↓
10. Backend streams MP3 file
    ↓
11. Frontend plays audio through AudioPlayer component
    ↓
12. User hears meme audio
```

### Timing Example

```
T=0s:     User says "That goal was amazing!"
T=0-3s:   Browser records audio
T=3s:     Browser sends chunk to server
T=3.2s:   Server receives chunk, saves to temp file
T=3.3s:   Whisper starts transcription
T=4.8s:   Whisper completes: "that goal was amazing"
T=4.9s:   Context Analyzer finds match: tags=["goal", "football"]
T=5.0s:   Trigger Engine: cooldown OK, probability OK
T=5.1s:   Server sends trigger message to client
T=5.2s:   Client receives message, requests audio
T=5.3s:   Audio starts playing
T=5.3-10s: Meme audio plays

Total latency: ~5 seconds (speech → audio playback)
```

**Latency Breakdown:**
- Recording: 3s (chunk size)
- Network: 0.1s (local network)
- Whisper: 1.5s (base model on RTX 4070)
- Analysis + Trigger: 0.2s
- Audio Fetch: 0.1s
- **Total: ~5s**

**Optimization Opportunities:**
- Reduce chunk size to 1-2s (lower latency but less context)
- Use smaller Whisper model (faster but less accurate)
- Stream Whisper output (not supported by current API)

---

## File Structure Guide

### Backend Structure

```
backend/
├── Dockerfile                 # Backend container config
├── requirements.txt           # Python dependencies
└── app/
    ├── main.py               # FastAPI app, routes, server config
    ├── websocket.py          # WebSocket handler, audio streaming
    ├── whisper_service.py    # Whisper model wrapper
    ├── context_analyzer.py   # Tag matching logic
    ├── trigger_engine.py     # Cooldown & probability engine
    ├── meme_manager.py       # File storage operations
    ├── database.py           # SQLite async operations
    └── models.py             # Pydantic data models
```

**Navigation Tips:**
- Audio processing flow: `websocket.py` → `whisper_service.py` → `context_analyzer.py` → `trigger_engine.py`
- API routes: All in `main.py`
- Database schema: See `database.py:init_db()`
- Data models: See `models.py`

---

### Frontend Structure

```
frontend/
├── Dockerfile                # Frontend container config
├── package.json              # NPM dependencies
├── vite.config.js            # Vite configuration
├── tailwind.config.js        # Tailwind configuration
├── postcss.config.js         # PostCSS configuration
├── index.html                # HTML entry point
└── src/
    ├── main.jsx              # React entry point
    ├── App.jsx               # Root component, routing
    ├── components/
    │   ├── SessionControl.jsx    # Main control panel
    │   ├── AudioPlayer.jsx       # Global audio player
    │   ├── Settings.jsx          # Settings form
    │   └── MemeLibrary.jsx       # Library management
    └── services/
        ├── api.js            # REST API client
        └── websocket.js      # WebSocket client
```

**Navigation Tips:**
- User flow: `App.jsx` → `SessionControl.jsx` → `websocket.js`
- Audio playback: `AudioPlayer.jsx`
- Backend communication: `services/api.js` and `services/websocket.js`
- UI components: All in `components/`

---

## Development Notes

### Local Development Setup

```bash
# 1. Clone repository
git clone https://github.com/badmuriss/sobub-ai.git
cd sobub-ai

# 2. Start with Docker Compose
docker-compose up --build

# 3. Access
# PC: http://localhost:5173
# Mobile: http://YOUR_PC_IP:5173
```

### Development Without Docker

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Note**: GPU support requires NVIDIA drivers and CUDA toolkit outside Docker.

---

### Testing Audio Processing

```bash
# Test Whisper directly
python -c "
from app.whisper_service import WhisperService
service = WhisperService()
text = service.transcribe('test.mp3')
print(text)
"

# Test context matching
python -c "
from app.context_analyzer import ContextAnalyzer
from app.models import Meme

analyzer = ContextAnalyzer()
memes = [Meme(id=1, filename='goal.mp3', tags=['goal', 'football'], created_at='')]
matches = analyzer.find_matches('That goal was amazing!', memes)
print([m.filename for m in matches])
"
```

---

### Database Inspection

```bash
# Access SQLite database
sqlite3 backend/data/memes.db

# Useful queries
SELECT * FROM memes;
SELECT * FROM settings;
SELECT COUNT(*) FROM memes;
SELECT tags FROM memes;
```

---

### Debugging WebSocket

**Backend logging:**
```python
# In websocket.py
print(f"Received audio chunk: {len(audio_data)} bytes")
print(f"Transcription: {text}")
print(f"Matches found: {len(matches)}")
```

**Frontend logging:**
```javascript
// In websocket.js
console.log('WebSocket connected');
console.log('Received message:', data);
console.log('Audio chunk size:', buffer.byteLength);
```

**Browser DevTools:**
- Network tab → WS filter → View WebSocket frames
- Console → See all WebSocket events

---

## Common Patterns

### Adding a New API Endpoint

**1. Define Pydantic model (if needed):**
```python
# models.py
class NewModel(BaseModel):
    field1: str
    field2: int
```

**2. Add database operation:**
```python
# database.py
async def get_new_data(db_path: str) -> NewModel:
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("SELECT * FROM table")
        row = await cursor.fetchone()
        return NewModel(field1=row[0], field2=row[1])
```

**3. Add route:**
```python
# main.py
@app.get("/api/newdata", response_model=NewModel)
async def get_new_data():
    data = await db.get_new_data(DATABASE_PATH)
    return data
```

**4. Add frontend API method:**
```javascript
// api.js
async getNewData() {
  const response = await fetch(`${API_URL}/api/newdata`);
  if (!response.ok) throw new Error('Failed to fetch');
  return response.json();
}
```

---

### Adding a New React Component

**1. Create component file:**
```jsx
// NewComponent.jsx
import React, { useState } from 'react';

const NewComponent = ({ prop1, prop2 }) => {
  const [state, setState] = useState(null);

  return (
    <div className="p-4">
      {/* Component UI */}
    </div>
  );
};

export default NewComponent;
```

**2. Add route (if needed):**
```jsx
// App.jsx
import NewComponent from './components/NewComponent';

<Route path="/new" element={<NewComponent />} />
```

---

### Modifying Whisper Model

```yaml
# docker-compose.yml
environment:
  - WHISPER_MODEL=small  # Change to: tiny, base, small, medium, large
```

**After changing:**
```bash
docker-compose down
docker-compose up --build
```

**First run will download new model (~300MB - 3GB depending on size)**

---

## Future Enhancements

### Short Term (Low Effort, High Value)

1. **Semantic Tag Matching**
   - Use sentence transformers for embedding-based matching
   - Match "car" with "automobile", "goal" with "score"
   - Library: `sentence-transformers`

2. **Tag Suggestions**
   - Analyze audio filename and suggest tags
   - Use simple keyword extraction
   - Library: `rake-nltk`

3. **Volume Normalization**
   - Normalize audio volume on upload
   - Prevent some memes being too loud/quiet
   - Library: `pydub`

4. **Connection Status Indicator**
   - Show real-time connection health
   - Display latency, packet loss
   - Alert on disconnection

5. **Trigger History**
   - Log all triggers with timestamp
   - Show "last played" for each meme
   - Add "skip" button during playback

---

### Medium Term (Moderate Effort)

1. **Multi-Language Support**
   - Whisper supports 100+ languages
   - Add language selector in settings
   - Tag matching needs language-specific logic

2. **Voice Activity Detection (VAD)**
   - Only process audio chunks with speech
   - Reduce Whisper calls by 50-80%
   - Library: `webrtcvad` or `silero-vad`

3. **Progressive Web App (PWA)**
   - Add service worker for offline support
   - Install as mobile app
   - Background audio playback

4. **Advanced Trigger Rules**
   - Time-based rules ("only on weekends")
   - Context chaining ("only after specific keywords")
   - Tag weighting ("football" = 2x weight)

5. **Audio Waveform Visualization**
   - Show real-time audio waveform during recording
   - Library: `wavesurfer.js`

---

### Long Term (High Effort)

1. **Multi-User Support**
   - User accounts and authentication
   - Personal libraries
   - Shared libraries with permissions

2. **Cloud Deployment**
   - Deploy to AWS/GCP/Azure
   - HTTPS with SSL certificates
   - Persistent storage (S3/Cloud Storage)

3. **Mobile App (Native)**
   - React Native or Flutter
   - Better mobile performance
   - Push notifications

4. **AI Voice Cloning**
   - Generate custom meme audio with AI voices
   - Library: `coqui-ai/TTS`

5. **Video Support**
   - Upload video memes (short clips)
   - Extract audio for matching
   - Play video on trigger

---

## Troubleshooting Guide

### GPU Not Detected

**Symptoms:**
- Whisper runs on CPU (very slow)
- Log shows: "CUDA not available"

**Solutions:**
1. Check NVIDIA driver: `nvidia-smi`
2. Check Docker GPU support: `docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi`
3. Restart Docker: `sudo systemctl restart docker`
4. Check docker-compose.yml has GPU config

---

### WebSocket Connection Fails

**Symptoms:**
- "WebSocket error" in console
- Can't start session

**Solutions:**
1. Check backend is running: `curl http://localhost:8000/api/status`
2. Check firewall: `sudo ufw allow 8000`
3. Check CORS settings in `main.py`
4. Check browser console for specific error

---

### No Audio Plays

**Symptoms:**
- Trigger received but no sound
- AudioPlayer shows file but silent

**Solutions:**
1. Check browser volume
2. Check system volume
3. Check audio file is valid: Play in VLC/media player
4. Check browser audio permissions
5. Open browser DevTools → Application → Check for autoplay policy

---

### Transcription Inaccurate

**Symptoms:**
- Wrong words transcribed
- Missing words

**Solutions:**
1. Improve audio quality: Better microphone, reduce background noise
2. Use larger Whisper model: Change `WHISPER_MODEL=small` or `medium`
3. Check microphone settings in browser
4. Ensure language matches (Whisper defaults to English auto-detect)

---

### High Memory Usage

**Symptoms:**
- Docker container uses >8GB RAM
- System slowdown

**Solutions:**
1. Use smaller Whisper model: `WHISPER_MODEL=tiny` or `base`
2. Limit Docker memory: Add to docker-compose.yml:
   ```yaml
   deploy:
     resources:
       limits:
         memory: 4G
   ```
3. Clean up temp files regularly (should be automatic)

---

### Mobile Can't Connect

**Symptoms:**
- Mobile browser can't access `http://PC_IP:5173`
- "Can't reach server"

**Solutions:**
1. Find PC IP: `ip addr show | grep "inet " | grep -v 127.0.0.1`
2. Check PC firewall: `sudo ufw allow 5173` and `sudo ufw allow 8000`
3. Ensure PC and mobile on same WiFi network
4. Check PC isn't in isolation mode (some corporate networks)
5. Try PC IP directly: `http://192.168.1.XXX:5173`

---

## Conclusion

This document provides comprehensive context for AI assistants working on the Sobub AI codebase. Key takeaways:

1. **Architecture**: Clean separation between frontend (React) and backend (FastAPI)
2. **Real-time**: WebSocket for low-latency audio streaming
3. **AI-Powered**: Whisper for accurate speech recognition
4. **Local-First**: Everything runs on user's machine, privacy-focused
5. **Mobile-Friendly**: Automatic network detection enables seamless mobile access

For further questions or clarifications, refer to the inline code comments and other documentation files (README.md, SETUP.md, ARCHITECTURE.md).

**Happy coding! 🚀**
