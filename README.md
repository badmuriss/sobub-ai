# Sobub AI

**S**ilence **O**ccasionally **B**roken **U**p **B**y **AI**

A context-aware ambient audio companion that listens to conversations and plays relevant meme audios based on detected topics and probability-based triggering.

## Features

- 🎤 Real-time speech recognition using Whisper (faster-whisper, GPU-accelerated)
- 🏷️ Multi-tag system for contextual audio matching
- 🎲 Configurable random triggering with cooldown
- 📱 Mobile-optimized web interface
- 🔒 Fully local AI processing (no external APIs)
- 🔐 HTTPS support for mobile microphone access
- 🐳 Docker containerized with NVIDIA GPU support
- 🎵 Custom audio library management
- 🌍 Multi-language support (English, Portuguese, Spanish, etc.)
- 📊 Real-time event log with match tracking

## Tech Stack

- **Backend**: Python 3.10 + FastAPI + faster-whisper
- **Frontend**: React 18 + Vite 7 + TailwindCSS
- **Database**: SQLite
- **Infrastructure**: Docker + NVIDIA Container Toolkit + Nginx (HTTPS)
- **AI**: CUDA 12.3 + cuDNN 9

## Prerequisites

- Docker & Docker Compose
- NVIDIA GPU (recommended for fast transcription)
- NVIDIA drivers + NVIDIA Container Toolkit
  - Installation guide: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html
  - Test: `docker run --rm --gpus all nvidia/cuda:12.3.2-base-ubuntu22.04 nvidia-smi`

## Quick Start

### 1. Clone and Start

```bash
git clone https://github.com/badmuriss/sobub-ai.git
cd sobub-ai
docker-compose up --build
```

SSL certificates are **auto-generated** on first startup - no manual steps needed!

### 2. Access the Application

**On PC:**
- `https://localhost` (HTTPS with self-signed cert)
- Accept the security warning (one-time, safe for local dev)

**On Mobile:**
1. Find your PC's IP: `hostname -I`
2. Access: `https://YOUR_PC_IP` (e.g., `https://192.168.1.100`)
3. Accept the security warning
4. Grant microphone permission

**Note:** HTTPS is required for microphone access on mobile devices.

### 3. Start Using

1. Click **Start Session** on the home screen
2. Allow microphone access
3. Start talking - Sobub AI listens and occasionally triggers relevant memes
4. Use **Settings** to:
   - Adjust cooldown period (default: 3 minutes)
   - Set trigger probability (default: 50%)
   - Change language (default: Portuguese)
   - Configure audio chunk length
   - Select Whisper model size

## How It Works

```
1. Browser captures microphone audio (WebM/Opus, configurable chunks)
2. Sent via WebSocket to backend
3. Whisper transcribes audio (GPU-accelerated)
4. Context analyzer matches transcription against meme tags
5. Trigger engine applies probability + cooldown logic
6. If triggered, audio is streamed back and played
7. Cooldown starts AFTER audio finishes playing
```

## Configuration

All settings are configurable via the web interface:

| Setting | Default | Description |
|---------|---------|-------------|
| **Cooldown** | 180s (3min) | Time between audio triggers |
| **Trigger Probability** | 50% | Chance to play when tags match |
| **Whisper Model** | base | Whisper model size (tiny/base/small/medium/large) |
| **Chunk Length** | 3s | Audio chunk duration for processing |
| **Language** | pt (Portuguese) | Transcription language (en, pt, es, etc.) |

## Project Structure

```
sobub-ai/
├── docker-compose.yml          # Orchestration with nginx, backend, frontend
├── nginx/
│   ├── Dockerfile
│   ├── conf/nginx.conf        # HTTPS reverse proxy config
│   ├── ssl/                   # Auto-generated SSL certificates
│   └── docker-entrypoint.sh   # Auto cert generation script
├── backend/
│   ├── Dockerfile             # CUDA 12.3 + cuDNN 9 + Python 3.10
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py           # FastAPI app + REST routes
│   │   ├── websocket.py      # WebSocket handler (audio streaming)
│   │   ├── whisper_service.py # faster-whisper integration
│   │   ├── context_analyzer.py # Tag matching logic
│   │   ├── trigger_engine.py  # Cooldown + probability engine
│   │   ├── meme_manager.py    # Audio file CRUD
│   │   ├── database.py        # SQLite operations
│   │   └── models.py          # Pydantic models
│   └── data/
│       ├── memes.db           # SQLite database
│       └── audio_files/       # Uploaded meme audio files
└── frontend/
    ├── Dockerfile             # Node 20 + Vite 7
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── App.jsx            # Root component + routing
        ├── components/
        │   ├── SessionControl.jsx  # Main session controls + event log
        │   ├── AudioPlayer.jsx     # Global audio playback
        │   └── Settings.jsx        # Settings management
        └── services/
            ├── api.js         # REST API client
            └── websocket.js   # WebSocket client + audio recording
```

## Troubleshooting

### Can't Connect from Mobile

1. Ensure PC and mobile are on the same WiFi
2. Check firewall:
   ```bash
   sudo ufw allow 443
   sudo ufw allow 80
   ```
3. Verify PC IP: `hostname -I`
4. Access `https://YOUR_PC_IP` and accept certificate warning

### Microphone Not Working

1. Verify you're using **HTTPS** (lock icon in browser)
2. Check browser permissions: Settings → Site Settings → Microphone
3. Try different browser (Chrome/Firefox work best)
4. Check browser console (F12) for errors

### Transcription Slow or Inaccurate

1. **Slow**: Use smaller model (Settings → Whisper Model → tiny/base)
2. **Inaccurate**: Use larger model (small/medium) or improve microphone quality
3. **Wrong language**: Change language in Settings

### GPU Not Detected

```bash
# Check NVIDIA drivers
nvidia-smi

# Check Docker GPU support
docker run --rm --gpus all nvidia/cuda:12.3.2-base-ubuntu22.04 nvidia-smi

# Restart Docker
sudo systemctl restart docker

# Check docker-compose.yml has runtime: nvidia
```

### Port Already in Use

```bash
# Check what's using ports
sudo lsof -i :443
sudo lsof -i :80

# Stop conflicting service or change ports in docker-compose.yml
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f nginx
```

## Development

### Backend Development (Native)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Note:** Requires CUDA toolkit installed for GPU support.

### Frontend Development (Native)

```bash
cd frontend
npm install
npm run dev  # Starts on http://localhost:5173
```

### Rebuilding Containers

```bash
# Rebuild all
docker-compose up --build

# Rebuild specific service
docker-compose up --build backend
docker-compose stop frontend && docker-compose rm -f frontend && docker-compose build --no-cache frontend && docker-compose up -d frontend
```

## Security Notes

**Development Use:**
- Self-signed SSL certificates are for local development only
- Certificate files (`nginx/ssl/*.pem`) are git-ignored
- Never deploy with self-signed certs to production

**Production Deployment:**
- Use proper domain with Let's Encrypt certificates
- Restrict CORS origins in `backend/app/main.py`
- Add authentication/authorization
- Use environment variables for secrets
- Enable rate limiting

## License

MIT

## Contributing

Contributions welcome! Feel free to open issues or submit PRs.

---

**Privacy Note**: This project runs entirely locally. No data is sent to external servers. All speech recognition happens on your machine with NVIDIA GPU acceleration.
