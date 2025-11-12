# Sobub AI - Deployment Checklist

## ✅ Pre-Deployment Checklist

### System Requirements
- [ ] Linux system (tested on Linux Mint)
- [ ] NVIDIA GPU with 4GB+ VRAM
- [ ] NVIDIA drivers installed (verify with `nvidia-smi`)
- [ ] Docker installed (verify with `docker --version`)
- [ ] Docker Compose installed (verify with `docker-compose --version`)
- [ ] NVIDIA Container Toolkit installed

### Network Setup
- [ ] PC has static local IP (or DHCP reservation)
- [ ] Firewall allows ports 5173 and 8000
- [ ] Phone/devices on same network as PC

---

## 🚀 Initial Deployment

### 1. Installation
- [ ] Clone/download project
- [ ] Create data directories: `mkdir -p backend/data/audio_files backend/models`
- [ ] Navigate to project: `cd sobub-ai`

### 2. First Build
```bash
- [ ] Run: docker-compose up --build
- [ ] Wait for "Whisper model loaded" message (~2-3 min)
- [ ] Check no errors in logs
```

### 3. GPU Verification
```bash
- [ ] Run: docker-compose exec backend nvidia-smi
- [ ] Verify GPU detected
- [ ] Check CUDA version: 12.1+
```

### 4. Access Test
- [ ] Open http://localhost:5173 on PC
- [ ] Check no console errors in browser
- [ ] Verify API docs at http://localhost:8000/docs

### 5. Network Access
- [ ] Find PC IP: `ip addr show | grep "inet "`
- [ ] Access from phone: `http://YOUR_PC_IP:5173`
- [ ] Test both Home and Settings pages

---

## 🎵 First Session Setup

### 1. Upload Test Audio
- [ ] Go to Settings page
- [ ] Upload at least 3 MP3 files
- [ ] Add descriptive tags to each
- [ ] Verify files appear in library

### 2. Configure Settings
- [ ] Set cooldown (start with 180s = 3min)
- [ ] Set probability (start with 40%)
- [ ] Save settings
- [ ] Verify settings persist

### 3. Test Session
- [ ] Go to Home page
- [ ] Click "Start Session"
- [ ] Allow microphone access
- [ ] Say words matching your tags
- [ ] Wait for transcription to appear
- [ ] Verify audio plays (check volume!)

---

## 🔧 Configuration Checklist

### Backend (.env if needed)
- [ ] `WHISPER_MODEL=base` (or small/medium)
- [ ] `DATABASE_PATH=/app/data/memes.db`
- [ ] `AUDIO_PATH=/app/data/audio_files`

### Frontend (vite config)
- [ ] API_URL points to correct backend
- [ ] WS_URL points to correct WebSocket
- [ ] Development server accessible on network

### Docker Compose
- [ ] GPU deployment section uncommented
- [ ] Correct port mappings
- [ ] Volume mounts configured
- [ ] Networks properly defined

---

## 🧪 Testing Checklist

### Functionality Tests
- [ ] Audio recording works
- [ ] Transcription appears in UI
- [ ] Context matching triggers memes
- [ ] Audio plays correctly
- [ ] Cooldown respects settings
- [ ] Probability works as expected

### Upload/CRUD Tests
- [ ] Upload MP3 succeeds
- [ ] Edit tags works
- [ ] Delete removes file
- [ ] Database updates correctly
- [ ] Files stored properly

### WebSocket Tests
- [ ] Connection establishes
- [ ] Reconnects on disconnect
- [ ] Messages send/receive
- [ ] Binary audio chunks work

### Settings Tests
- [ ] Load current settings
- [ ] Update cooldown
- [ ] Update probability
- [ ] Changes persist
- [ ] Trigger engine updates

---

## 🐛 Common Issues & Fixes

### Issue: GPU Not Detected
```bash
- [ ] Check: docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
- [ ] Fix: Reinstall nvidia-container-toolkit
- [ ] Restart: sudo systemctl restart docker
```

### Issue: WebSocket Connection Failed
```bash
- [ ] Check: Backend running (docker-compose logs backend)
- [ ] Check: Firewall (sudo ufw status)
- [ ] Check: CORS settings in backend/app/main.py
- [ ] Try: Different browser (Chrome recommended)
```

### Issue: No Audio Plays
```bash
- [ ] Check: Browser audio not muted
- [ ] Check: Device volume up
- [ ] Check: Console for errors
- [ ] Check: Audio files exist (ls backend/data/audio_files/)
- [ ] Try: Play meme manually via API
```

### Issue: Microphone Not Working
```bash
- [ ] Check: Browser permissions granted
- [ ] Check: System microphone working
- [ ] Try: Different browser
- [ ] Try: HTTPS connection (required for some browsers)
```

### Issue: Whisper Model Download Fails
```bash
- [ ] Check: Internet connection
- [ ] Try: Manual download inside container
- [ ] Run: docker-compose exec backend python -c "import whisper; whisper.load_model('base')"
```

---

## 📊 Performance Verification

### Expected Performance
- [ ] Transcription latency: 1-2 seconds
- [ ] Total trigger latency: 4-5 seconds
- [ ] GPU memory usage: ~2GB
- [ ] CPU usage: <20% idle

### Monitoring Commands
```bash
# GPU usage
- [ ] nvidia-smi -l 1

# Container stats
- [ ] docker stats

# Logs
- [ ] docker-compose logs -f
```

---

## 🔒 Security Checklist

### For Development
- [ ] Only use on trusted local network
- [ ] Don't expose to public internet
- [ ] Keep firewall enabled

### For Production (if applicable)
- [ ] Add authentication
- [ ] Implement HTTPS
- [ ] Restrict CORS origins
- [ ] Add rate limiting
- [ ] Set up reverse proxy (nginx)
- [ ] Regular security updates

---

## 📝 Documentation Review

Before going live:
- [ ] Read README.md
- [ ] Read SETUP.md
- [ ] Read QUICKSTART.md
- [ ] Read ARCHITECTURE.md (optional)
- [ ] Understand tag strategy
- [ ] Know troubleshooting steps

---

## 🎯 Post-Deployment

### Daily Operations
- [ ] Check logs for errors
- [ ] Monitor disk usage (audio files)
- [ ] Verify GPU health
- [ ] Backup database if needed

### Maintenance
- [ ] Update Docker images periodically
- [ ] Clean up old/unused audio files
- [ ] Review and optimize tags
- [ ] Update settings based on usage

### Optimization
- [ ] Adjust cooldown based on conversation pace
- [ ] Tune probability for desired frequency
- [ ] Review tag effectiveness
- [ ] Consider upgrading Whisper model if needed

---

## 🆘 Emergency Procedures

### Complete Reset
```bash
1. [ ] docker-compose down
2. [ ] Backup: cp -r backend/data backend/data.backup
3. [ ] Remove database: rm backend/data/memes.db
4. [ ] docker-compose up --build
5. [ ] Re-upload audio files
```

### Restore from Backup
```bash
1. [ ] docker-compose down
2. [ ] cp -r backend/data.backup/* backend/data/
3. [ ] docker-compose up
```

### Contact/Support
- [ ] Check GitHub issues
- [ ] Review logs thoroughly
- [ ] Document error messages
- [ ] Include system specs in bug reports

---

## ✨ Success Criteria

You're ready when:
- ✅ App accessible from phone
- ✅ Audio uploads successfully
- ✅ Transcription works reliably
- ✅ Memes trigger appropriately
- ✅ No errors in logs
- ✅ Performance is acceptable
- ✅ You understand how to troubleshoot

---

**Happy Sobub-ing! 🎉**

Remember: Start with conservative settings (5min cooldown, 30% probability) and adjust based on experience!
