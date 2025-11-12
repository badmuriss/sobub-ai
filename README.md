# Sobub AI

**S**ilence **O**ccasionally **B**roken **U**p **B**y **AI**

A context-aware ambient audio companion that listens to conversations and occasionally plays relevant meme audios based on detected topics.

## Features

- 🎤 Real-time speech recognition using Whisper (local, GPU-accelerated)
- 🏷️ Multi-tag system for contextual audio matching
- 🎲 Configurable random triggering with cooldown
- 📱 Mobile-optimized web interface with automatic network detection
- 🔒 Fully local AI processing (no external APIs)
- 🐳 Docker containerized for easy deployment
- 🎵 Custom audio library management
- 🌐 Zero-config mobile connectivity (auto-detects PC backend)

## Architecture

- **Backend**: Python + FastAPI + OpenAI Whisper
- **Frontend**: React + Vite + TailwindCSS
- **Database**: SQLite
- **Deployment**: Docker + Docker Compose with NVIDIA GPU support

## Prerequisites

- Docker & Docker Compose
- NVIDIA GPU with drivers installed
- NVIDIA Container Toolkit ([see GPU_SETUP.md for installation](./GPU_SETUP.md))

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/badmuriss/sobub-ai.git
cd sobub-ai
```

2. Build and run with Docker Compose:
```bash
docker-compose up --build
```

3. Access the app:
- **From PC**: http://localhost:5173
- **From mobile**: http://YOUR_PC_IP:5173 (automatic backend detection)
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Usage

1. Open the web interface on your phone/device
2. Click the **Start Session** button on the home screen
3. Allow microphone access when prompted
4. Sobub AI will listen and occasionally play relevant meme audios
5. Use the Settings page to:
   - Upload new audio files with tags
   - Adjust cooldown period (default: 5 minutes)
   - Set trigger probability (default: 30%)
   - Manage your audio library

## Project Structure

```
sobub-ai/
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py
│   │   ├── websocket.py
│   │   ├── whisper_service.py
│   │   ├── context_analyzer.py
│   │   ├── meme_manager.py
│   │   ├── trigger_engine.py
│   │   ├── database.py
│   │   └── models.py
│   └── data/
│       ├── memes.db
│       └── audio_files/
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx
│       ├── components/
│       └── services/
└── README.md
```

## Configuration

Settings can be adjusted via the web interface:

- **Cooldown**: Time between audio plays (in seconds)
- **Trigger Probability**: Chance of playing audio when context matches (0-100%)
- **Whisper Model**: Using `base` model (good balance of speed/accuracy)

## How It Works

1. Browser captures microphone audio and sends chunks via WebSocket
2. Whisper transcribes audio in real-time (GPU-accelerated)
3. Context analyzer matches transcribed text against audio tags
4. Trigger engine applies probability + cooldown logic
5. Matched audio is sent back and played through the device speaker

## Development

### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

## License

MIT

## Contributing

Contributions welcome! Feel free to open issues or submit PRs.

---

**Note**: This project runs entirely locally. No data is sent to external servers.
