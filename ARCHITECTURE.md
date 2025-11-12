# Sobub AI - Technical Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         User's Phone/Device                      │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    React Frontend (Port 5173)               │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │ │
│  │  │ SessionControl│  │   Settings   │  │ AudioPlayer  │    │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘    │ │
│  │         │                  │                  │            │ │
│  │         └──────────────────┴──────────────────┘            │ │
│  │                           │                                │ │
│  │         ┌─────────────────┴─────────────────┐             │ │
│  │         │                                     │             │ │
│  │    WebSocket                            REST API           │ │
│  │  (Audio Streaming)                  (CRUD Operations)      │ │
│  └────────│─────────────────────────────────────│─────────────┘ │
└───────────│─────────────────────────────────────│───────────────┘
            │                                     │
            │                                     │
     ┌──────▼─────────────────────────────────────▼──────┐
     │          PC Server (Docker Containers)            │
     │                                                    │
     │  ┌──────────────────────────────────────────┐    │
     │  │    FastAPI Backend (Port 8000)           │    │
     │  │                                           │    │
     │  │  ┌────────────────┐  ┌────────────────┐ │    │
     │  │  │ WebSocket      │  │ REST API       │ │    │
     │  │  │ Handler        │  │ Routes         │ │    │
     │  │  └───────┬────────┘  └───────┬────────┘ │    │
     │  │          │                   │           │    │
     │  │          │                   │           │    │
     │  │  ┌───────▼───────────────────▼────────┐ │    │
     │  │  │      Core Processing Layer         │ │    │
     │  │  │                                     │ │    │
     │  │  │  ┌──────────────────────────────┐  │ │    │
     │  │  │  │    Whisper Service           │  │ │    │
     │  │  │  │  (Speech Recognition)        │  │ │    │
     │  │  │  │  - GPU Accelerated (CUDA)    │  │ │    │
     │  │  │  │  - Base Model (~140MB)       │  │ │    │
     │  │  │  └──────────────────────────────┘  │ │    │
     │  │  │              │                      │ │    │
     │  │  │              ▼                      │ │    │
     │  │  │  ┌──────────────────────────────┐  │ │    │
     │  │  │  │   Context Analyzer           │  │ │    │
     │  │  │  │  (Tag Matching)              │  │ │    │
     │  │  │  │  - Keyword Extraction        │  │ │    │
     │  │  │  │  - Multi-tag Support         │  │ │    │
     │  │  │  └──────────────────────────────┘  │ │    │
     │  │  │              │                      │ │    │
     │  │  │              ▼                      │ │    │
     │  │  │  ┌──────────────────────────────┐  │ │    │
     │  │  │  │   Trigger Engine             │  │ │    │
     │  │  │  │  (Decision Logic)            │  │ │    │
     │  │  │  │  - Cooldown Management       │  │ │    │
     │  │  │  │  - Probability Check         │  │ │    │
     │  │  │  │  - Random Selection          │  │ │    │
     │  │  │  └──────────────────────────────┘  │ │    │
     │  │  │              │                      │ │    │
     │  │  │              ▼                      │ │    │
     │  │  │  ┌──────────────────────────────┐  │ │    │
     │  │  │  │    Meme Manager              │  │ │    │
     │  │  │  │  (Audio File Management)     │  │ │    │
     │  │  │  │  - File Storage              │  │ │    │
     │  │  │  │  - Tag Management            │  │ │    │
     │  │  │  └──────────────────────────────┘  │ │    │
     │  │  │              │                      │ │    │
     │  │  └──────────────┼──────────────────────┘ │    │
     │  │                 │                        │    │
     │  └─────────────────┼────────────────────────┘    │
     │                    │                             │
     │  ┌─────────────────▼──────────────────────┐     │
     │  │        Data Layer                      │     │
     │  │                                         │     │
     │  │  ┌──────────────┐   ┌──────────────┐  │     │
     │  │  │   SQLite     │   │ Audio Files  │  │     │
     │  │  │   Database   │   │  (MP3s)      │  │     │
     │  │  │              │   │              │  │     │
     │  │  │ - Memes      │   │ /data/       │  │     │
     │  │  │ - Settings   │   │ audio_files/ │  │     │
     │  │  │ - Metadata   │   │              │  │     │
     │  │  └──────────────┘   └──────────────┘  │     │
     │  └─────────────────────────────────────────┘     │
     │                                                   │
     │  ┌────────────────────────────────────────┐      │
     │  │      NVIDIA GPU (RTX 4070 Super)       │      │
     │  │    - CUDA 12.1                         │      │
     │  │    - Whisper Inference                 │      │
     │  └────────────────────────────────────────┘      │
     └───────────────────────────────────────────────────┘
```

## Data Flow

### 1. Audio Recording & Transcription
```
User Speech
    ↓
Browser MediaRecorder (3s chunks)
    ↓
WebSocket → Backend
    ↓
Whisper Service (GPU)
    ↓
Transcribed Text
    ↓
WebSocket → Frontend (display transcription)
```

### 2. Context Matching & Triggering
```
Transcribed Text
    ↓
Context Analyzer
    ↓ (extract keywords)
Match Against Tags
    ↓
Matched Tags → Get Matching Memes
    ↓
Trigger Engine
    ├─ Check Cooldown (active?)
    ├─ Check Probability (random < threshold?)
    └─ Select Random Meme
         ↓
    Trigger Event
         ↓
WebSocket → Frontend
    ↓
Play Audio (meme_id)
    ↓
Increment Play Count
```

### 3. Audio Upload
```
User Selects File + Tags
    ↓
Multipart Form Data
    ↓
REST API (POST /api/memes)
    ↓
Meme Manager
    ├─ Save File (sanitize filename)
    └─ Create DB Entry (tags, metadata)
         ↓
Return Meme Object
    ↓
Update Frontend List
```

## Technology Stack

### Backend
- **Language**: Python 3.10
- **Framework**: FastAPI
- **AI Model**: OpenAI Whisper (base)
- **GPU**: CUDA 12.1 (PyTorch)
- **Database**: SQLite (aiosqlite)
- **WebSocket**: websockets library

### Frontend
- **Framework**: React 18
- **Build Tool**: Vite
- **Styling**: TailwindCSS
- **Routing**: React Router v6
- **Audio**: Web Audio API
- **Recording**: MediaRecorder API

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **GPU Runtime**: NVIDIA Container Toolkit
- **Networking**: Bridge network (Docker)

## Component Details

### Backend Components

#### 1. Whisper Service
```python
- Model: base (74M parameters)
- Device: CUDA (GPU)
- Sample Rate: 16kHz
- Latency: ~1-2s per chunk
- Language: English (configurable)
```

#### 2. Context Analyzer
```python
- Algorithm: Keyword extraction + partial matching
- Stop Words: Filtered out
- Multi-word Tags: Supported
- Case-insensitive: Yes
```

#### 3. Trigger Engine
```python
- State Management: In-memory
- Cooldown: Timestamp-based
- Probability: Random uniform [0, 100)
- Selection: Random choice from matches
```

#### 4. Meme Manager
```python
- File Storage: /app/data/audio_files/
- Filename Sanitization: Yes
- Duplicate Handling: Auto-rename
- Format: MP3 only
```

### Frontend Components

#### 1. SessionControl
- Manages WebSocket connection
- Controls MediaRecorder
- Displays transcriptions
- Shows session status

#### 2. AudioPlayer
- Plays triggered memes
- Handles audio URLs
- Auto-cleanup on completion

#### 3. Settings
- Settings management
- Audio upload
- Library CRUD operations

#### 4. MemeLibrary
- Display all memes
- Edit tags
- Delete memes
- Upload interface

## Database Schema

### Memes Table
```sql
CREATE TABLE memes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    tags TEXT NOT NULL,  -- JSON array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    play_count INTEGER DEFAULT 0
);
```

### Settings Table
```sql
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Default settings:
-- cooldown_seconds: 300
-- trigger_probability: 30
-- whisper_model: base
```

## API Contract

### WebSocket Protocol

#### Client → Server
```json
{
  "type": "ping"
}
```

Binary: Audio chunks (WebM/Opus)

#### Server → Client
```json
{
  "type": "transcription",
  "text": "transcribed text"
}

{
  "type": "trigger",
  "meme_id": 123,
  "filename": "audio.mp3",
  "matched_tags": ["football", "goal"]
}

{
  "type": "pong"
}
```

### REST API

#### GET /api/memes
Response:
```json
[
  {
    "id": 1,
    "filename": "goal.mp3",
    "tags": ["football", "goal", "celebration"],
    "created_at": "2025-01-01T12:00:00",
    "play_count": 5
  }
]
```

#### POST /api/memes
Request: multipart/form-data
- file: audio file
- tags: comma-separated string

#### PUT /api/settings
Request:
```json
{
  "cooldown_seconds": 300,
  "trigger_probability": 30.0
}
```

## Performance Characteristics

### Latency
- Audio chunk: 3 seconds
- Whisper inference: 1-2 seconds
- Total latency: 4-5 seconds
- WebSocket overhead: <100ms

### Resource Usage
- **GPU VRAM**: ~2GB (Whisper model)
- **CPU RAM**: ~1GB (backend)
- **Disk**: ~200MB + audio files
- **Network**: ~50KB/s (audio streaming)

### Scalability
- Single user: Optimal
- Multiple users: Would need session management
- Concurrent requests: Limited by GPU

## Security Considerations

### Current Implementation
- ⚠️ No authentication
- ⚠️ CORS: Allow all (development)
- ✅ Local processing (no external APIs)
- ✅ Filename sanitization
- ⚠️ No rate limiting

### Recommended for Production
- Add JWT authentication
- Restrict CORS origins
- Implement rate limiting
- Add HTTPS (reverse proxy)
- Validate file types server-side
- Add user sessions

## Future Enhancements

### Planned Features
1. Multi-language support
2. Semantic matching (sentence-transformers)
3. Voice activity detection
4. Custom Whisper models
5. Audio preprocessing
6. Statistics dashboard
7. Shared libraries
8. Cloud deployment guide

### Technical Improvements
1. Better audio buffering
2. Caching layer for frequent queries
3. Background transcription queue
4. Optimized tag indexing
5. Batch audio uploads
6. Export/import library

## Deployment Architecture

### Development (Current)
```
Docker Compose → Local Network
```

### Production (Recommended)
```
User → HTTPS (443)
       ↓
    Nginx (Reverse Proxy + SSL)
       ↓
    Docker Network
       ├→ Frontend Container
       └→ Backend Container (GPU)
```

## Monitoring & Debugging

### Logs
```bash
# Real-time logs
docker-compose logs -f

# Backend only
docker-compose logs -f backend | grep -i error

# GPU usage
nvidia-smi -l 1
```

### Metrics to Track
- Transcription latency
- Trigger success rate
- WebSocket connections
- GPU utilization
- Memory usage
- Error rates

---

**Document Version**: 1.0  
**Last Updated**: November 2025  
**Project**: Sobub AI
