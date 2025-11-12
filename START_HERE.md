# 🚀 Getting Started with Sobub AI

## Your Project is Complete!

All files have been created and are ready to use. Here's what to do next:

---

## 📦 What You Have

A complete AI-powered ambient audio system with:
- ✅ **Backend**: Python + FastAPI + Whisper AI
- ✅ **Frontend**: React + Vite + TailwindCSS  
- ✅ **Database**: SQLite
- ✅ **Docker**: Full containerization with GPU support
- ✅ **Documentation**: 6 comprehensive guides

**Total**: 33 files, ~2,000 lines of code

---

## ⚡ Quick Start (5 Minutes)

### 1. Prerequisites Check
```bash
# Check Docker
docker --version

# Check NVIDIA drivers (if you have GPU)
nvidia-smi

# Check Docker Compose
docker-compose --version
```

### 2. Install NVIDIA Container Toolkit (One-Time Setup)
```bash
# For Ubuntu/Linux Mint
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

### 3. Start the Application
```bash
cd sobub-ai
docker-compose up --build
```

**Wait for**: "Whisper model loaded successfully" (~2-3 minutes first time)

### 4. Access the App
- **On PC**: Open http://localhost:5173
- **On Phone**: 
  1. Find your PC IP: `ip addr show | grep "inet " | grep -v 127.0.0.1`
  2. Open http://YOUR_PC_IP:5173 on phone browser

### 5. Upload Audio & Test
1. Click **Settings** → Upload MP3 files with tags
2. Click **Home** → Click **Start Session**
3. Allow microphone access
4. Start talking!

---

## 📚 Documentation Overview

### For First-Time Setup
1. **START HERE** → `QUICKSTART.md` - Quick reference card
2. **DETAILED** → `SETUP.md` - Complete installation guide
3. **CHECKLIST** → `DEPLOYMENT_CHECKLIST.md` - Step-by-step verification

### For Understanding the System
4. **OVERVIEW** → `README.md` - Project description & features
5. **TECHNICAL** → `ARCHITECTURE.md` - How everything works
6. **SUMMARY** → `PROJECT_SUMMARY.md` - Complete project overview

---

## 🎯 Recommended Reading Order

1. **QUICKSTART.md** (5 min) - Get the basics
2. **SETUP.md** (15 min) - Follow installation steps
3. Start the app and experiment!
4. **DEPLOYMENT_CHECKLIST.md** (10 min) - Verify everything works
5. **ARCHITECTURE.md** (optional) - Deep dive into internals

---

## 🎵 Your First Meme Setup

### Example: Football Theme
1. Find 3-5 short MP3 clips (3-10 seconds each)
2. Upload each with tags:
   - `goal_celebration.mp3` → Tags: `football, goal, celebration, score`
   - `miss.mp3` → Tags: `football, miss, shot, fail`
   - `referee_whistle.mp3` → Tags: `football, referee, foul, penalty`

3. Settings:
   - Cooldown: 180 seconds (3 minutes)
   - Probability: 40%

4. Start session and talk about football!

---

## 🔧 Common First-Time Issues

### Issue: "GPU not detected"
```bash
# Verify GPU works with Docker
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# If it fails:
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
docker-compose down
docker-compose up --build
```

### Issue: "Cannot access from phone"
```bash
# Check firewall
sudo ufw status

# Allow ports if needed
sudo ufw allow 5173
sudo ufw allow 8000

# Verify PC and phone on same network
```

### Issue: "Whisper model won't download"
```bash
# Download manually
docker-compose exec backend python -c "import whisper; whisper.load_model('base')"
```

---

## 💡 Pro Tips

### Tag Strategy
- Use **3-5 tags per audio**
- Mix general + specific: `football, goal, celebration`
- Keep tags lowercase
- Use common words people actually say

### Settings Sweet Spots
- **Casual conversation**: 5min cooldown, 30% probability
- **Active gaming**: 2min cooldown, 50% probability  
- **Background ambient**: 10min cooldown, 20% probability

### Audio Files
- **Best duration**: 3-10 seconds
- **Keep volume consistent** across files
- **Test each audio** before using
- **Organize by theme** (sports, gaming, cooking, etc.)

---

## 🎮 Usage Scenarios

### During a Game
- Start session on phone
- Place phone near TV/speakers
- App listens to game commentary
- Plays relevant memes when topics match
- Cooldown prevents spam

### Cooking Together
- Phone on kitchen counter
- Discusses recipe steps
- Plays chef/cooking memes
- Adds fun to cooking session

### Work Meeting
- Casual team meeting
- Light-hearted environment
- Occasional meme breaks
- Long cooldown (10min)

---

## 🚨 Emergency Commands

### Stop Everything
```bash
docker-compose down
```

### Complete Reset
```bash
docker-compose down
rm backend/data/memes.db
docker-compose up --build
# Re-upload your audio files
```

### View Logs
```bash
# All logs
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100
```

---

## 📊 Success Metrics

You'll know it's working when:
- ✅ No errors in logs
- ✅ Can access from phone
- ✅ Microphone captures audio
- ✅ Transcriptions appear
- ✅ Memes play occasionally
- ✅ Settings save correctly

---

## 🎓 Learning Path

### Beginner (Day 1)
- Get it running
- Upload 5 audio files
- Test basic functionality
- Adjust cooldown/probability

### Intermediate (Week 1)
- Build themed audio library (20+ files)
- Optimize tag strategy
- Test different scenarios
- Fine-tune settings

### Advanced (Month 1)
- Experiment with Whisper models
- Add custom features
- Deploy to multiple devices
- Share your setup!

---

## 🤝 Community & Support

### Need Help?
1. Check documentation (SETUP.md especially)
2. Review logs: `docker-compose logs -f`
3. Search GitHub issues
4. Open new issue with:
   - Your OS & GPU info
   - Complete error logs
   - Steps to reproduce

### Want to Contribute?
- Fork the repository
- Make improvements
- Submit pull requests
- Share your audio library themes
- Report bugs & suggest features

---

## 🎉 You're Ready!

Everything is set up and ready to go. Just:

```bash
cd sobub-ai
docker-compose up --build
```

Then open http://localhost:5173 and start having fun!

---

## 📞 Quick Reference Card

```
START:    docker-compose up -d
STOP:     docker-compose down
LOGS:     docker-compose logs -f
RESTART:  docker-compose restart
STATUS:   docker-compose ps

FRONTEND: http://localhost:5173
BACKEND:  http://localhost:8000
API DOCS: http://localhost:8000/docs
```

---

**Welcome to Sobub AI!** 🎵🤖

*Silence Occasionally Broken Up By AI*

Have fun and enjoy breaking the silence with context-aware memes!
