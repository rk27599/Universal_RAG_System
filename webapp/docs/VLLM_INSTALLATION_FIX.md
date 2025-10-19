# vLLM Installation Fix for WSL/CUDA Environment

## Problem

The vLLM package has version conflicts:
- vLLM 0.11.0 requires `torch==2.8.0` (CPU-only version)
- But we need PyTorch with CUDA support for GPU inference
- Current system: PyTorch 2.5.1+cu121 (CUDA enabled)

## Solution Options

### Option 1: Use Compatible vLLM Version (Recommended)

Install an older vLLM version that works with PyTorch 2.5.1+cu121:

```bash
source venv/bin/activate

# Install vLLM 0.6.0 (compatible with PyTorch 2.5.x)
pip install vllm==0.6.0 --no-deps
pip install ray>=2.9.0

# Verify installation
python -c "import vllm; print(vllm.__version__)"
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
```

### Option 2: Install vLLM from Source (Advanced)

If you need the latest vLLM features:

```bash
source venv/bin/activate

# Clone vLLM repository
cd /tmp
git clone https://github.com/vllm-project/vllm.git
cd vllm

# Install with CUDA support
pip install -e . --no-build-isolation

# Return to project
cd /home/rkpatel/RAG
```

### Option 3: Use Docker (Easiest for Production)

vLLM provides official Docker images with all dependencies:

```bash
# Pull official vLLM image with CUDA
docker pull vllm/vllm-openai:latest

# Run vLLM server
docker run --gpus all \
    -p 8001:8000 \
    --ipc=host \
    vllm/vllm-openai:latest \
    --model mistralai/Mistral-7B-Instruct-v0.2 \
    --host 0.0.0.0 \
    --port 8000

# Access at http://localhost:8001
```

### Option 4: Stick with Ollama (Simplest)

If vLLM installation is too complex, Ollama works perfectly:

```bash
# Ollama is already configured and working
# Default in .env:
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434

# Start Ollama
ollama serve

# Pull model
ollama pull mistral

# Your RAG system will work immediately
```

## Quick Test After Installation

### Test vLLM (if using Option 1 or 2):

```bash
source venv/bin/activate

# Start vLLM server manually
python -m vllm.entrypoints.openai.api_server \
    --model mistralai/Mistral-7B-Instruct-v0.2 \
    --host localhost \
    --port 8001

# In another terminal, test:
curl http://localhost:8001/v1/models
```

### Test with RAG System:

```bash
# Update .env
LLM_PROVIDER=vllm  # or "ollama"

# Restart backend
cd webapp/backend
python -m uvicorn main:app --reload
```

## Recommended Approach

For your setup, I recommend **Option 4 (Stick with Ollama)** because:

1. ✅ **Already working** - No installation hassles
2. ✅ **Sufficient for development** - Good performance for single user
3. ✅ **Easy to maintain** - Simple model management
4. ✅ **Works out of the box** - No CUDA/dependency conflicts

**Switch to vLLM later when:**
- You have multiple concurrent users (5+)
- Performance becomes a bottleneck
- You're ready for production deployment

## Current System Status

```
✅ PyTorch: 2.5.1+cu121 (CUDA enabled)
✅ GPU: NVIDIA GeForce RTX 3070 (8GB)
✅ CUDA: 13.0
✅ Ollama: Working and configured
⚠️  vLLM: Installation requires specific setup
```

## Alternative: Pre-built vLLM Environment

If you really need vLLM, create a separate conda environment:

```bash
# Create new conda environment
conda create -n vllm-env python=3.10
conda activate vllm-env

# Install vLLM with CUDA
pip install vllm

# Run vLLM from this environment
python -m vllm.entrypoints.openai.api_server \
    --model mistralai/Mistral-7B-Instruct-v0.2 \
    --host localhost \
    --port 8001
```

Then your RAG system (in the main venv) can connect to vLLM running in the separate conda environment.

## Summary

**For immediate use**: Stick with Ollama (it's working perfectly)
**For production later**: Use Docker-based vLLM (Option 3)
**For development**: Use vLLM 0.6.0 (Option 1) or Ollama

The RAG system supports both providers seamlessly - just change one environment variable!
