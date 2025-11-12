# GPU Setup Guide - NVIDIA Container Toolkit

This guide will help you fix the error: `Error response from daemon: could not select device driver "nvidia" with capabilities: [[gpu]]`

---

## Problem Diagnosis

✅ **Your NVIDIA GPU driver is working** (version 570.195.03, CUDA 12.8)
❌ **Docker cannot access the GPU** (NVIDIA Container Toolkit not installed)

---

## Solution: Install NVIDIA Container Toolkit

Follow these steps to enable GPU support in Docker:

### Step 1: Add NVIDIA Container Toolkit Repository

```bash
# Download and add the NVIDIA GPG key
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

# Add the repository to your sources
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
```

### Step 2: Install the Toolkit

```bash
# Update package list
sudo apt-get update

# Install NVIDIA Container Toolkit
sudo apt-get install -y nvidia-container-toolkit
```

### Step 3: Configure Docker Runtime

```bash
# Configure Docker to use NVIDIA runtime
sudo nvidia-ctk runtime configure --runtime=docker

# Restart Docker daemon
sudo systemctl restart docker
```

### Step 4: Verify Installation

```bash
# Test GPU access from Docker
docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi
```

**Expected output**: Should show your GPU information (RTX 4070 Super) inside the container.

---

## Alternative Method (If Above Fails)

If the above method doesn't work, try this alternative:

```bash
# Add Docker GPG key and repository (if not already done)
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Install nvidia-docker2
sudo apt-get update
sudo apt-get install -y nvidia-docker2

# Restart Docker
sudo systemctl restart docker
```

---

## Testing Sobub AI with GPU

After installing the NVIDIA Container Toolkit, test your setup:

### 1. Stop any running containers
```bash
cd /home/badmuriss/Documents/dev-projects/sobub-ai
docker-compose down
```

### 2. Rebuild with updated dependencies
```bash
docker-compose up --build
```

### 3. Check backend logs for GPU detection
```bash
docker-compose logs backend | grep -i cuda
```

**Expected output**: Should show CUDA is available and which GPU is being used.

---

## Troubleshooting

### Issue: "nvidia-smi not found" inside container
**Solution**: Your base image doesn't have nvidia-smi. This is normal for base images. The GPU will still work for PyTorch.

### Issue: "CUDA out of memory"
**Solutions**:
- Close other GPU-intensive applications (browsers, games, etc.)
- Use a smaller Whisper model: Change `WHISPER_MODEL=tiny` in docker-compose.yml
- Monitor GPU memory: `watch -n 1 nvidia-smi`

### Issue: Docker build fails with "E: Unable to locate package"
**Solution**: The PPA might not be added correctly. Try:
```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
```

### Issue: "Permission denied" errors
**Solution**: Add your user to docker group:
```bash
sudo usermod -aG docker $USER
newgrp docker  # Or logout and login again
```

---

## Verify GPU is Actually Being Used

Once containers are running, check if PyTorch can see the GPU:

```bash
# Execute Python inside the backend container
docker exec -it sobub-backend python3 -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"
```

**Expected output**:
```
CUDA available: True
GPU: NVIDIA GeForce RTX 4070 Super
```

---

## What Changed in the Update

### 1. **requirements.txt** - All dependencies updated:
- FastAPI: 0.104.1 → 0.121.1
- PyTorch: 2.1.0 → 2.9.0
- NumPy: 1.24.3 → 2.3.4 (major version!)
- And 8 more packages...

### 2. **Dockerfile** - Python upgraded:
- Python: 3.10 → 3.11 (required for NumPy 2.x)
- CUDA base image: 12.1.0 → 12.4.0 (closer to your 12.8 driver)

### 3. **Compatibility Verified**:
- ✅ PyTorch 2.9.0 fully supports NumPy 2.x
- ✅ All packages support Python 3.11
- ✅ No breaking API changes expected

---

## Performance Benefits After Update

- **Faster inference**: PyTorch 2.9.0 has optimizations for RTX 40-series GPUs
- **Better stability**: Bug fixes in all major dependencies
- **Future-proof**: All dependencies are now current as of Nov 2025
- **Security**: Latest versions include security patches

---

## Quick Command Reference

```bash
# Install NVIDIA Container Toolkit (all in one)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg && \
distribution=$(. /etc/os-release;echo $ID$VERSION_ID) && \
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list && \
sudo apt-get update && \
sudo apt-get install -y nvidia-container-toolkit && \
sudo nvidia-ctk runtime configure --runtime=docker && \
sudo systemctl restart docker

# Test GPU access
docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi

# Rebuild Sobub AI
cd /home/badmuriss/Documents/dev-projects/sobub-ai
docker-compose down
docker-compose up --build

# Check if GPU is being used
docker exec -it sobub-backend python3 -c "import torch; print('CUDA:', torch.cuda.is_available())"
```

---

## Need Help?

If you encounter issues:

1. Check Docker logs: `docker-compose logs -f backend`
2. Verify GPU driver: `nvidia-smi`
3. Check Docker GPU access: `docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi`
4. Ensure Docker service is running: `sudo systemctl status docker`

---

## Summary

**What you need to do**:
1. Run the commands in "Step 1-4" above
2. Rebuild your containers: `docker-compose up --build`
3. Verify GPU is working

**What was updated**:
- ✅ All Python dependencies (11 packages)
- ✅ Python version (3.10 → 3.11)
- ✅ Docker base image (CUDA 12.1 → 12.4)

**Time estimate**: 5-10 minutes for NVIDIA toolkit installation and rebuild
