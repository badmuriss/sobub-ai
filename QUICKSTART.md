# Sobub AI - Quick Start

## 🚀 Get Started in 3 Steps

### 1. Start the App
```bash
cd sobub-ai
docker-compose up --build
```
Wait for "Whisper model loaded" message (~2-3 minutes first time)

### 2. Access the App
- **On PC**: http://localhost:5173
- **On Phone**: http://YOUR_PC_IP:5173
  - Find your PC IP: `ip addr show | grep "inet "`
  - **✨ Auto-detection**: Frontend automatically connects to correct backend (no config needed!)

### 3. First Session
1. Open Settings → Upload MP3s with tags
2. Go Home → Click "Start Session"
3. Allow microphone access
4. Start talking!

---

## 📱 Quick Commands

### Start/Stop
```bash
docker-compose up -d      # Start in background
docker-compose down       # Stop
docker-compose restart    # Restart
```

### View Logs
```bash
docker-compose logs -f backend    # Backend logs
docker-compose logs -f frontend   # Frontend logs
```

### Clean Restart
```bash
docker-compose down
docker-compose up --build
```

---

## 🎯 How It Works

1. **You talk** → Microphone captures audio
2. **Whisper transcribes** → Text extracted (local GPU)
3. **Tags matched** → Looks for relevant topics
4. **Random chance** → Cooldown + probability check
5. **Meme plays** → Audio plays through your device

---

## ⚙️ Settings Explained

### Cooldown (seconds)
- **60** = 1 minute between plays
- **300** = 5 minutes (default)
- **600** = 10 minutes

### Trigger Probability (%)
- **10-20%** = Rare surprises
- **30-40%** = Balanced (default: 30%)
- **60-80%** = Frequent memes

### Tag Examples
✅ **Good**: `football, soccer, goal, sports, celebration`
❌ **Bad**: `funny_video_1, meme123`

---

## 🎵 Audio Tips

- **Duration**: 3-10 seconds ideal
- **Format**: MP3 only
- **Volume**: Keep consistent
- **Tags**: 3-5 tags per audio

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| No GPU detected | Install nvidia-container-toolkit |
| WebSocket fails | Check firewall/CORS settings |
| No audio plays | Check browser permissions |
| Mic not working | Try Chrome/Firefox |

### Check GPU
```bash
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

---

## 📊 API Endpoints

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 🎪 Example Use Cases

### Football Watch Party
- Tags: `football, goal, miss, penalty, referee, celebration`
- Cooldown: 180s (3 min)
- Probability: 40%

### Cooking Stream
- Tags: `cooking, recipe, chef, ingredients, kitchen, delicious`
- Cooldown: 240s (4 min)
- Probability: 30%

### Gaming Session
- Tags: `gaming, win, lose, rage, epic, noob, headshot`
- Cooldown: 120s (2 min)
- Probability: 50%

---

## 📁 Project Structure

```
sobub-ai/
├── backend/           Python + Whisper + FastAPI
├── frontend/          React + Vite + TailwindCSS
├── docker-compose.yml Docker configuration
├── README.md          Project overview
└── SETUP.md          Detailed setup guide
```

---

## 🆘 Need Help?

1. Check SETUP.md for detailed instructions
2. View logs: `docker-compose logs -f`
3. Restart everything: `docker-compose down && docker-compose up --build`
4. Open issue on GitHub

---

**Made with ❤️ using Whisper + AI**

*Silence Occasionally Broken Up By AI*
