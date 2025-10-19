# vLLM Installation Guide

Complete installation guide for adding vLLM support to the RAG system.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Installation Methods](#installation-methods)
3. [Verification](#verification)
4. [Configuration](#configuration)
5. [Common Issues](#common-issues)

---

## Prerequisites

### Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **GPU** | 1x NVIDIA GPU (16GB VRAM) | 2+ NVIDIA GPUs (24GB+ VRAM each) |
| **RAM** | 32GB system RAM | 64GB+ system RAM |
| **Storage** | 50GB free space | 100GB+ free space |
| **CPU** | 8 cores | 16+ cores |

### Software Requirements

```bash
# Check your system

# 1. NVIDIA GPU
nvidia-smi
# Expected: GPU name, driver version, CUDA version

# 2. CUDA Toolkit
nvcc --version
# Expected: CUDA 11.8+ or 12.1+

# 3. Python version
python --version
# Expected: Python 3.10-3.12

# 4. Current PyTorch (if installed)
python -c "import torch; print(torch.__version__)"
# Note: vLLM may conflict with existing PyTorch
```

**Supported Systems:**
- ✅ Ubuntu 20.04+, 22.04 LTS
- ✅ WSL 2 (Windows Subsystem for Linux)
- ✅ CentOS 7+, Rocky Linux 8+
- ⚠️  macOS (limited support, CPU only)

---

## Installation Methods

### Method 1: Docker (Recommended) ⭐

**Pros:**
- No dependency conflicts
- Easiest to set up
- Pre-configured environment
- Isolated from system Python

**Cons:**
- Requires Docker + nvidia-docker
- Slightly larger disk usage

#### Steps:

```bash
# 1. Install Docker (if not installed)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Logout and login again

# 2. Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker

# 3. Test NVIDIA Docker
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
# Expected: GPU info displayed

# 4. Pull vLLM Docker image
docker pull vllm/vllm-openai:latest

# 5. Run vLLM server
docker run --gpus all \
    -p 8001:8000 \
    --ipc=host \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    vllm/vllm-openai:latest \
    --model mistralai/Mistral-7B-Instruct-v0.2 \
    --host 0.0.0.0 \
    --port 8000

# 6. Test connection
curl http://localhost:8001/v1/models
```

**For Multi-GPU:**
```bash
docker run --gpus all \
    -p 8001:8000 \
    --ipc=host \
    --shm-size=10g \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    vllm/vllm-openai:latest \
    --model meta-llama/Llama-2-13b-chat-hf \
    --host 0.0.0.0 \
    --port 8000 \
    --tensor-parallel-size 2
```

---

### Method 2: Native Installation (Advanced)

**Pros:**
- Full control over dependencies
- Better integration with existing Python env
- Easier debugging

**Cons:**
- May conflict with existing PyTorch
- Requires manual dependency management
- More complex setup

#### Option A: Fresh Virtual Environment (Recommended)

```bash
cd /home/rkpatel/RAG

# Create new venv for vLLM
python3.10 -m venv venv-vllm
source venv-vllm/bin/activate

# Install PyTorch 2.5+ with CUDA 12.1
pip install torch==2.5.1 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install vLLM
pip install vllm>=0.6.0

# Install Ray for multi-GPU
pip install ray>=2.9.0

# Verify installation
python -c "import vllm; print(f'vLLM version: {vllm.__version__}')"
python -c "import torch; print(f'PyTorch: {torch.__version__}, CUDA: {torch.cuda.is_available()}')"
```

#### Option B: Existing venv (May have conflicts)

```bash
cd /home/rkpatel/RAG
source venv/bin/activate

# Check current PyTorch
pip show torch

# Option 1: Install compatible vLLM version
pip install vllm==0.6.0 --no-deps
pip install ray>=2.9.0

# Option 2: Upgrade PyTorch (may break other deps)
pip install --upgrade torch==2.5.1 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install vllm>=0.6.0 ray>=2.9.0
```

**⚠️ Warning:** If you see dependency conflicts, use Method 3 (Conda) instead.

---

### Method 3: Separate Conda Environment

**Pros:**
- Complete isolation from RAG system
- No conflicts with existing Python packages
- Clean dependency management

**Cons:**
- vLLM runs in separate environment
- Requires Anaconda/Miniconda

#### Steps:

```bash
# 1. Install Miniconda (if not installed)
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
# Follow prompts, then restart terminal

# 2. Create conda environment
conda create -n vllm-env python=3.10
conda activate vllm-env

# 3. Install CUDA toolkit
conda install cuda -c nvidia/label/cuda-12.1.0

# 4. Install PyTorch
pip install torch==2.5.1 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 5. Install vLLM
pip install vllm>=0.6.0 ray>=2.9.0

# 6. Verify
python -c "import vllm, torch; print(f'vLLM: {vllm.__version__}, CUDA: {torch.cuda.is_available()}')"
```

**Running vLLM from Conda:**
```bash
# Activate conda env
conda activate vllm-env

# Start vLLM server
python -m vllm.entrypoints.openai.api_server \
    --model mistralai/Mistral-7B-Instruct-v0.2 \
    --host localhost \
    --port 8001

# In another terminal, run RAG backend (main venv)
cd /home/rkpatel/RAG
source venv/bin/activate
cd webapp/backend
python -m uvicorn main:app --reload
```

---

## Verification

### 1. Test vLLM Installation

```bash
# Activate appropriate environment
source venv-vllm/bin/activate  # or conda activate vllm-env

# Test import
python -c "import vllm; print(f'✅ vLLM {vllm.__version__} installed')"

# Test CUDA
python -c "import torch; print(f'✅ CUDA available: {torch.cuda.is_available()}')"
python -c "import torch; print(f'✅ GPU count: {torch.cuda.device_count()}')"
```

### 2. Start vLLM Server

```bash
# Using setup script
cd /home/rkpatel/RAG/webapp
./scripts/setup_vllm.sh mistralai/Mistral-7B-Instruct-v0.2 1 1

# Or manually
python -m vllm.entrypoints.openai.api_server \
    --model mistralai/Mistral-7B-Instruct-v0.2 \
    --host localhost \
    --port 8001
```

**Expected output:**
```
INFO: Loading model mistralai/Mistral-7B-Instruct-v0.2
INFO: Initializing vLLM engine...
INFO: Using 1 GPU(s) for inference
INFO: Model loaded successfully
INFO: Server started at http://localhost:8001
```

### 3. Test vLLM API

```bash
# Test model listing
curl http://localhost:8001/v1/models

# Test generation
curl http://localhost:8001/v1/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "mistralai/Mistral-7B-Instruct-v0.2",
        "prompt": "Hello, how are you?",
        "max_tokens": 50
    }'
```

### 4. Test with RAG Backend

```bash
# Update .env
cd /home/rkpatel/RAG/webapp/backend
echo "LLM_PROVIDER=vllm" >> .env
echo "VLLM_BASE_URL=http://localhost:8001" >> .env

# Start backend
python -m uvicorn main:app --reload

# Check logs for:
# ✅ Security settings validation passed (LLM Provider: vllm)
# ✅ LLM Service initialized: vLLM (http://localhost:8001)
```

---

## Configuration

### Update Backend `.env`

Edit `/home/rkpatel/RAG/webapp/backend/.env`:

```bash
# LLM Provider Settings
LLM_PROVIDER=vllm  # Change from "ollama" to "vllm"

# vLLM Configuration
VLLM_BASE_URL=http://localhost:8001
VLLM_MODEL_PATH=/models
VLLM_GPU_COUNT=1  # Set to your GPU count
VLLM_TENSOR_PARALLEL_SIZE=1  # Must divide GPU_COUNT evenly

# Keep Ollama settings for fallback
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_MODEL=mistral
```

### Model Selection

**For Single 16GB GPU:**
```bash
mistralai/Mistral-7B-Instruct-v0.2
meta-llama/Llama-2-7b-chat-hf
```

**For Single 24GB GPU:**
```bash
meta-llama/Llama-2-13b-chat-hf
mistralai/Mixtral-8x7B-Instruct-v0.1
```

**For 2+ GPUs:**
```bash
# Set in .env
VLLM_GPU_COUNT=2
VLLM_TENSOR_PARALLEL_SIZE=2

# Use 13B+ models
meta-llama/Llama-2-13b-chat-hf
codellama/CodeLlama-34b-Instruct-hf
```

---

## Common Issues

### Issue 1: "ModuleNotFoundError: No module named 'vllm'"

**Solution:**
```bash
# Ensure you're in the correct environment
source venv-vllm/bin/activate  # or conda activate vllm-env

# Reinstall vLLM
pip install vllm>=0.6.0
```

### Issue 2: "CUDA not available" or "No CUDA GPUs found"

**Solution:**
```bash
# Check NVIDIA driver
nvidia-smi

# Reinstall PyTorch with CUDA
pip uninstall torch torchvision torchaudio
pip install torch==2.5.1 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Verify CUDA
python -c "import torch; print(torch.cuda.is_available())"
```

### Issue 3: "Version conflict between vLLM and PyTorch"

**Solution A: Use Docker** (easiest)
```bash
docker pull vllm/vllm-openai:latest
# Follow Docker installation steps above
```

**Solution B: Create fresh Conda environment**
```bash
conda create -n vllm-clean python=3.10
conda activate vllm-clean
pip install vllm>=0.6.0 ray>=2.9.0
```

### Issue 4: "Out of memory" during installation

**Solution:**
```bash
# Clear pip cache
pip cache purge

# Install with no cache
pip install --no-cache-dir vllm>=0.6.0

# Close other applications
# Ensure at least 8GB RAM available
```

### Issue 5: "ImportError: cannot import name 'LLM'"

**Solution:**
```bash
# Check vLLM version
pip show vllm

# Upgrade to latest
pip install --upgrade vllm>=0.6.0

# Or use specific version
pip install vllm==0.6.3
```

### Issue 6: "Ray initialization failed"

**Solution:**
```bash
# Install/upgrade Ray
pip install --upgrade ray>=2.9.0

# Clear Ray temp files
rm -rf /tmp/ray/*

# Restart vLLM server
```

---

## Next Steps

After successful installation:

1. **Read**: [VLLM_COMPLETE_GUIDE.md](VLLM_COMPLETE_GUIDE.md) for usage
2. **Configure**: Performance tuning for your hardware
3. **Test**: Send test queries through the web interface
4. **Monitor**: Check GPU utilization with `nvidia-smi`
5. **Optimize**: Adjust batch size and parallelism

For troubleshooting, see [VLLM_TROUBLESHOOTING.md](VLLM_TROUBLESHOOTING.md).

---

## Installation Checklist

- [ ] Prerequisites verified (GPU, CUDA, Python)
- [ ] Installation method chosen (Docker/Native/Conda)
- [ ] vLLM installed successfully
- [ ] PyTorch with CUDA verified
- [ ] vLLM server starts without errors
- [ ] API test successful (`curl` test)
- [ ] `.env` file updated with `LLM_PROVIDER=vllm`
- [ ] Backend restart shows vLLM initialization
- [ ] Test query works through web interface
- [ ] GPU utilization visible in `nvidia-smi`

**Congratulations!** You've successfully installed vLLM support. 🎉
