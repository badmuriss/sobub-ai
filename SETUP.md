# Sobub AI - Setup Guide

## Prerequisites

Before you begin, ensure you have the following installed:

1. **Docker & Docker Compose**
   ```bash
   # Verify installation
   docker --version
   docker-compose --version
   ```

2. **NVIDIA GPU Drivers** (for GPU acceleration)
   ```bash
   # Verify NVIDIA driver
   nvidia-smi
   ```

3. **NVIDIA Container Toolkit**
   ```bash
   # Install on Linux
   distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
   curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
   curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
   
   sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
   sudo systemctl restart docker
   
   # Verify installation
   docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
   ```

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/badmuriss/sobub-ai.git
   cd sobub-ai
   ```

2. **Create necessary directories**
   ```bash
   mkdir -p backend/data/audio_files
   mkdir -p backend/models
   ```

3. **Build and start the containers**
   ```bash
   docker-compose up --build
   ```

   This will:
   - Build the backend with GPU support
   - Download the Whisper base model (~140MB on first run)
   - Build the frontend
   - Start both services

4. **Access the application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## First Time Setup

1. **Access from your phone**
   - Find your PC's local IP address:
     ```bash
     ip addr show | grep "inet " | grep -v 127.0.0.1
     ```
   - On your phone, navigate to: `http://YOUR_PC_IP:5173`

   **✨ Automatic Network Detection**: The frontend automatically detects which backend to connect to based on how you access it. No manual configuration needed! When you access the app from your phone, it automatically connects to your PC's backend.

2. **Upload some meme audio files**
   - Go to Settings page
   - Upload MP3 files with relevant tags
   - Example tags: `football, goal, celebration` or `cooking, recipe, kitchen`

3. **Configure settings**
   - Adjust cooldown period (default: 5 minutes)
   - Set trigger probability (default: 30%)

4. **Start a session**
   - Go to Home page
   - Click "Start Session"
   - Allow microphone access
   - Start talking!

## Usage Tips

### Tag Strategy
- Use **multiple specific tags** per audio file
- Mix **general** and **specific** tags:
  - Good: `football, goal, celebration, sports, win`
  - Bad: `video1, funny, meme`
- Use **lowercase** tags for consistency
- Common tags work better: `football` vs `american-football`

### Cooldown & Probability
- **Low cooldown (1-3 min) + High probability (60-80%)**: More frequent memes
- **High cooldown (5-10 min) + Low probability (20-40%)**: Occasional surprises
- Adjust based on your conversation pace

### Audio Files
- Use **short clips** (3-10 seconds work best)
- Keep **volume levels consistent** across files
- MP3 format only (for now)

## Troubleshooting

### GPU Not Detected
**See [GPU_SETUP.md](./GPU_SETUP.md) for detailed GPU troubleshooting.**

Quick fix:
```bash
# Check if NVIDIA runtime is available
docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi

# If it fails, install nvidia-container-toolkit (see GPU_SETUP.md)
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### Whisper Model Download Issues
```bash
# Manually download model
docker-compose exec backend python -c "import whisper; whisper.load_model('base')"
```

### WebSocket Connection Failed
- Check firewall settings
- Ensure both frontend and backend are running
- Verify URLs in browser console

### No Audio Playing
- Check browser audio permissions
- Ensure device volume is up
- Check browser console for errors
- Verify audio file exists in backend

### Microphone Not Working
- Grant microphone permissions in browser
- Try a different browser (Chrome/Firefox work best)
- Check system microphone settings

## Development

### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Viewing Logs
```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Frontend only
docker-compose logs -f frontend
```

## Project Structure

```
sobub-ai/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── main.py            # FastAPI app & routes
│   │   ├── websocket.py       # WebSocket handler
│   │   ├── whisper_service.py # Whisper integration
│   │   ├── context_analyzer.py # Tag matching
│   │   ├── trigger_engine.py  # Cooldown & probability
│   │   ├── meme_manager.py    # Audio file management
│   │   ├── database.py        # SQLite operations
│   │   └── models.py          # Data models
│   └── data/
│       ├── memes.db           # SQLite database
│       └── audio_files/       # MP3 files
├── frontend/                   # React frontend
│   └── src/
│       ├── components/        # React components
│       ├── services/          # API & WebSocket clients
│       └── App.jsx            # Main app
└── docker-compose.yml         # Docker orchestration
```

## API Endpoints

### Memes
- `GET /api/memes` - List all memes
- `POST /api/memes` - Upload new meme
- `GET /api/memes/{id}` - Get meme details
- `PUT /api/memes/{id}` - Update meme tags
- `DELETE /api/memes/{id}` - Delete meme
- `GET /api/memes/{id}/audio` - Get audio file

### Settings
- `GET /api/settings` - Get settings
- `PUT /api/settings` - Update settings

### Status
- `GET /api/status` - Get trigger engine status
- `GET /api/tags` - Get all unique tags

### WebSocket
- `WS /ws/{client_id}` - Audio streaming & triggers

## Advanced Configuration

### Changing Whisper Model
Edit `docker-compose.yml`:
```yaml
environment:
  - WHISPER_MODEL=small  # Options: tiny, base, small, medium, large
```

### Custom Port Mapping
Edit `docker-compose.yml`:
```yaml
ports:
  - "3000:5173"  # Frontend
  - "8080:8000"  # Backend
```

### Production Deployment
1. Update CORS settings in `backend/app/main.py`
2. Build production frontend: `npm run build`
3. Use reverse proxy (nginx) for HTTPS
4. Set proper environment variables

## Performance

- **Whisper base model**: ~1-2 seconds latency on RTX 4070
- **Memory usage**: ~2GB VRAM, ~1GB RAM
- **CPU usage**: Minimal (GPU handles inference)

## Security Notes

- Run on trusted networks only (no authentication built-in)
- Audio is processed locally (no external API calls)
- Consider adding authentication for public deployments

## Contributing

Feel free to submit issues and pull requests!

## License

MIT License - see LICENSE file for details
