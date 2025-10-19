# vLLM Troubleshooting Guide

Comprehensive troubleshooting guide for vLLM integration issues.

## Table of Contents
1. [Installation Issues](#installation-issues)
2. [Runtime Errors](#runtime-errors)
3. [Performance Issues](#performance-issues)
4. [Connection Issues](#connection-issues)
5. [Model Loading Issues](#model-loading-issues)
6. [Multi-GPU Issues](#multi-gpu-issues)
7. [Integration Issues](#integration-issues)
8. [Debugging Tools](#debugging-tools)

---

## Installation Issues

### Error: "Could not find a version that satisfies the requirement vllm"

**Cause:** Python version incompatible or pip index issue

**Solution:**
```bash
# Check Python version (must be 3.10-3.12)
python --version

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Try with specific version
pip install vllm==0.6.3

# Or use conda
conda create -n vllm-env python=3.10
conda activate vllm-env
pip install vllm
```

---

### Error: "torch 2.8.0 is required but you have 2.5.1+cu121"

**Cause:** vLLM wants CPU-only PyTorch, but you need CUDA

**Solution:**
```bash
# Install compatible vLLM version
pip uninstall vllm
pip install vllm==0.6.0 --no-deps
pip install ray>=2.9.0

# Verify CUDA still works
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
```

**Alternative: Use Docker** (recommended)
```bash
docker pull vllm/vllm-openai:latest
# No dependency conflicts!
```

---

### Error: "CUDA version mismatch" or "libcudart.so.12.1: cannot open shared object file"

**Cause:** vLLM compiled for different CUDA version

**Solution:**
```bash
# Check your CUDA version
nvidia-smi  # Look at "CUDA Version" in top right

# Install matching PyTorch
# For CUDA 12.1:
pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cu121

# For CUDA 11.8:
pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cu118

# Reinstall vLLM
pip install --upgrade vllm>=0.6.0
```

---

### Error: "No module named 'vllm.entrypoints.openai.api_server'"

**Cause:** Old vLLM version or incomplete installation

**Solution:**
```bash
# Uninstall completely
pip uninstall vllm -y
pip cache purge

# Reinstall latest version
pip install vllm>=0.6.3

# Verify installation
python -c "import vllm; print(vllm.__version__)"
```

---

## Runtime Errors

### Error: "CUDA out of memory"

**Symptoms:**
```
RuntimeError: CUDA out of memory. Tried to allocate 2.00 GiB
```

**Solutions:**

**1. Reduce GPU memory usage:**
```bash
python -m vllm.entrypoints.openai.api_server \
    --model mistralai/Mistral-7B-Instruct-v0.2 \
    --gpu-memory-utilization 0.7 \  # Reduce from default 0.9
    --max-model-len 2048  # Reduce context length
```

**2. Use smaller model:**
```bash
# Instead of 13B, use 7B
--model mistralai/Mistral-7B-Instruct-v0.2
```

**3. Enable tensor parallelism** (if you have multiple GPUs):
```bash
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-2-13b-chat-hf \
    --tensor-parallel-size 2  # Split across 2 GPUs
```

**4. Clear GPU memory:**
```bash
# Kill existing vLLM processes
pkill -9 python
# Or
ps aux | grep vllm | awk '{print $2}' | xargs kill -9

# Restart vLLM
./scripts/setup_vllm.sh <model> 1 1
```

---

### Error: "KeyError: 'choices'" or "No response from vLLM"

**Cause:** API request format mismatch

**Solution:**
```bash
# Test vLLM API manually
curl http://localhost:8001/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "mistralai/Mistral-7B-Instruct-v0.2",
        "messages": [
            {"role": "user", "content": "Hello"}
        ],
        "max_tokens": 100
    }'

# If this works, issue is in RAG backend integration
# Check logs for detailed error messages
```

---

### Error: "Segmentation fault (core dumped)"

**Cause:** GPU driver issue or memory corruption

**Solution:**
```bash
# 1. Update NVIDIA driver
sudo apt-get update
sudo apt-get install --reinstall nvidia-driver-XXX  # Your driver version

# 2. Check CUDA installation
nvcc --version
nvidia-smi

# 3. Reinstall vLLM from scratch
pip uninstall vllm torch -y
pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cu121
pip install vllm>=0.6.3

# 4. Test with minimal example
python -c "from vllm import LLM; llm = LLM('mistralai/Mistral-7B-Instruct-v0.2')"
```

---

## Performance Issues

### Issue: "Slow generation speed (< 10 tokens/sec)"

**Diagnostics:**
```bash
# Check GPU utilization
nvidia-smi -l 1  # Update every second
# Expected: 80-100% GPU utilization during generation
```

**Solutions:**

**If GPU utilization is LOW (<50%):**
```bash
# Increase batch size
python -m vllm.entrypoints.openai.api_server \
    --model mistralai/Mistral-7B-Instruct-v0.2 \
    --max-num-seqs 128 \  # Increase from default 256
    --max-num-batched-tokens 4096
```

**If GPU utilization is HIGH but speed is slow:**
```bash
# 1. Check tensor cores are being used
nvidia-smi dmon -s pucvmet
# Look for "tensor" activity

# 2. Reduce context length
--max-model-len 2048  # Faster than 4096

# 3. Use FP16/BF16 precision
--dtype float16  # Or bfloat16 for newer GPUs
```

**If multiple requests are queuing:**
```bash
# Enable continuous batching (should be default)
# Increase max sequences
--max-num-seqs 256
```

---

### Issue: "High latency for first request (>30 seconds)"

**Cause:** Model loading time (normal on first request)

**Solutions:**
```bash
# 1. Pre-load model on server start (automatic)
# First request will be slow, subsequent requests fast

# 2. Keep vLLM server running
# Don't restart for each query

# 3. Use model quantization (smaller model loads faster)
--quantization awq  # If model supports it
```

---

### Issue: "Throughput lower than expected"

**Expected Throughput (Mistral 7B on RTX 3070):**
- Single user: ~50 tokens/sec
- 10 concurrent users: ~5 tokens/sec per user (50 total)

**Diagnostics:**
```bash
# Monitor vLLM metrics
curl http://localhost:8001/metrics

# Check request queue
tail -f logs/vllm_*.log | grep "queue"
```

**Optimization:**
```bash
python -m vllm.entrypoints.openai.api_server \
    --model mistralai/Mistral-7B-Instruct-v0.2 \
    --max-num-seqs 256 \  # Higher for more concurrency
    --max-num-batched-tokens 8192 \  # Larger batches
    --gpu-memory-utilization 0.95  # Use more GPU memory
```

---

## Connection Issues

### Error: "Connection refused" to vLLM server

**Diagnostics:**
```bash
# 1. Check if vLLM is running
ps aux | grep vllm
lsof -i :8001  # Check port 8001

# 2. Test connection
curl http://localhost:8001/v1/models

# 3. Check logs
tail -f logs/vllm_*.log
```

**Solutions:**

**If vLLM not running:**
```bash
# Start vLLM
./scripts/setup_vllm.sh mistralai/Mistral-7B-Instruct-v0.2 1 1
```

**If vLLM running but connection fails:**
```bash
# Check firewall
sudo ufw status
sudo ufw allow 8001

# Check if binding to correct host
# vLLM should start with --host localhost (or 0.0.0.0)
```

**If port conflict:**
```bash
# Find process using port
lsof -i :8001

# Kill it
kill -9 <PID>

# Or use different port
python -m vllm.entrypoints.openai.api_server --port 8002
# Update VLLM_BASE_URL in .env
```

---

### Error: "Timeout waiting for vLLM to start"

**Cause:** Model download or GPU initialization taking too long

**Solution:**
```bash
# 1. Check logs
tail -f logs/vllm_*.log

# 2. Increase timeout in setup script (if using)
# Edit scripts/setup_vllm.sh
MAX_RETRIES=120  # Increase from 60

# 3. Pre-download model
pip install huggingface-hub
huggingface-cli download mistralai/Mistral-7B-Instruct-v0.2

# 4. Check disk space (models are large)
df -h
```

---

## Model Loading Issues

### Error: "Model not found" or "Failed to load model"

**Cause:** Model doesn't exist on Hugging Face or requires authentication

**Solution:**
```bash
# 1. Verify model exists
# Go to https://huggingface.co/<model-name>

# 2. For gated models (like Llama 2)
huggingface-cli login
# Enter your Hugging Face token

# 3. Use correct model name
--model meta-llama/Llama-2-7b-chat-hf  # Correct
# NOT: --model llama2  # Wrong
```

---

### Error: "Model size exceeds available memory"

**Symptoms:**
```
Model weights: 13GB, Available GPU memory: 8GB
```

**Solutions:**
```bash
# 1. Use smaller model
--model mistralai/Mistral-7B-Instruct-v0.2  # ~6GB

# 2. Use quantization (if supported)
--quantization awq  # 4-bit quantization

# 3. Enable tensor parallelism
--tensor-parallel-size 2  # Split across 2 GPUs

# 4. Use CPU offloading (slow but works)
# Not recommended for production
```

---

## Multi-GPU Issues

### Error: "Tensor parallel size must divide GPU count"

**Cause:** Invalid tensor parallelism configuration

**Examples:**
```bash
# ❌ Wrong: 3 GPUs, parallel size 2
VLLM_GPU_COUNT=3
VLLM_TENSOR_PARALLEL_SIZE=2

# ✅ Correct options for 3 GPUs:
VLLM_TENSOR_PARALLEL_SIZE=1  # Use 1 GPU
VLLM_TENSOR_PARALLEL_SIZE=3  # Use all 3 GPUs
```

**Solution:**
```bash
# For N GPUs, tensor_parallel_size must be: 1, 2, 4, 8, etc.
# AND must evenly divide N

# 2 GPUs: use 1 or 2
# 4 GPUs: use 1, 2, or 4
# 8 GPUs: use 1, 2, 4, or 8
```

---

### Error: "Ray initialization failed" for multi-GPU

**Solution:**
```bash
# 1. Install/upgrade Ray
pip install --upgrade ray>=2.9.0

# 2. Clear Ray temp files
rm -rf /tmp/ray/*

# 3. Set environment variables
export RAY_DEDUP_LOGS=0
export RAY_memory_monitor_refresh_ms=0

# 4. Start vLLM with Ray backend
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-2-13b-chat-hf \
    --tensor-parallel-size 2 \
    --distributed-executor-backend ray
```

---

### Issue: "Only 1 GPU being used" when multiple GPUs available

**Diagnostics:**
```bash
# Monitor all GPUs
watch -n 1 nvidia-smi

# Should show usage on multiple GPUs
```

**Solution:**
```bash
# 1. Set CUDA_VISIBLE_DEVICES
export CUDA_VISIBLE_DEVICES=0,1  # Use GPUs 0 and 1

# 2. Set tensor parallel size
--tensor-parallel-size 2

# 3. Verify in logs
tail -f logs/vllm_*.log | grep "tensor"
# Should show: "Using 2 GPUs with tensor parallelism"
```

---

## Integration Issues

### Error: "LLM Service Factory: Invalid provider 'vllm'"

**Cause:** Old code or typo in configuration

**Solution:**
```bash
# 1. Check .env file
cat webapp/backend/.env | grep LLM_PROVIDER
# Should be: LLM_PROVIDER=vllm (lowercase)

# 2. Restart backend
cd webapp/backend
python -m uvicorn main:app --reload

# 3. Check logs
# Should see: "✅ LLM Service initialized: vLLM (http://localhost:8001)"
```

---

### Error: "Backend still using Ollama after switching to vLLM"

**Cause:** .env file not reloaded or cached

**Solution:**
```bash
# 1. Verify .env
cat webapp/backend/.env | grep LLM_PROVIDER

# 2. Force reload
pkill -9 -f "uvicorn main:app"
cd webapp/backend
python -m uvicorn main:app --reload

# 3. Check initialization logs
# First few lines should show:
# "Security settings validation passed (LLM Provider: vllm)"
```

---

### Issue: "Responses working but using Ollama API format"

**Cause:** LLM_PROVIDER not set correctly

**Verification:**
```bash
# Check which service is loaded
cd webapp/backend
python -c "
from core.config import Settings
settings = Settings()
print(f'Provider: {settings.LLM_PROVIDER}')
"

# Should output: Provider: vllm
```

---

## Debugging Tools

### 1. Enable Detailed Logging

```bash
# Start vLLM with debug logging
python -m vllm.entrypoints.openai.api_server \
    --model mistralai/Mistral-7B-Instruct-v0.2 \
    --log-level debug

# Backend logging
cd webapp/backend
export LOG_LEVEL=DEBUG
python -m uvicorn main:app --reload --log-level debug
```

### 2. Monitor GPU Usage

```bash
# Real-time GPU monitoring
watch -n 1 nvidia-smi

# Detailed metrics
nvidia-smi dmon -s pucvmet -d 1

# GPU memory timeline
nvidia-smi --query-gpu=timestamp,memory.used --format=csv -l 1
```

### 3. Test vLLM API Directly

```bash
# List models
curl http://localhost:8001/v1/models | jq

# Test completion
curl http://localhost:8001/v1/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "mistralai/Mistral-7B-Instruct-v0.2",
        "prompt": "Hello, world!",
        "max_tokens": 50
    }' | jq

# Test chat
curl http://localhost:8001/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "mistralai/Mistral-7B-Instruct-v0.2",
        "messages": [
            {"role": "user", "content": "What is Python?"}
        ],
        "max_tokens": 100
    }' | jq
```

### 4. Check vLLM Health

```bash
# View vLLM metrics
curl http://localhost:8001/metrics

# View version
curl http://localhost:8001/version

# Test health endpoint (if available)
curl http://localhost:8001/health
```

### 5. Logs Analysis

```bash
# Backend logs
tail -f logs/app.log

# vLLM logs
tail -f logs/vllm_*.log

# Search for errors
grep -i error logs/vllm_*.log
grep -i "out of memory" logs/vllm_*.log
```

---

## Common Workflows

### Workflow 1: Fresh Install Troubleshooting

```bash
# 1. Verify prerequisites
nvidia-smi
nvcc --version
python --version

# 2. Clean install
pip uninstall vllm torch -y
pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cu121
pip install vllm>=0.6.3 ray>=2.9.0

# 3. Test installation
python -c "import vllm, torch; print(f'vLLM: {vllm.__version__}, CUDA: {torch.cuda.is_available()}')"

# 4. Start server
./scripts/setup_vllm.sh mistralai/Mistral-7B-Instruct-v0.2 1 1

# 5. Test API
curl http://localhost:8001/v1/models

# 6. Update config
echo "LLM_PROVIDER=vllm" >> webapp/backend/.env

# 7. Restart backend
cd webapp/backend
python -m uvicorn main:app --reload
```

### Workflow 2: Switching from Ollama to vLLM

```bash
# 1. Verify Ollama works
curl http://localhost:11434/api/tags

# 2. Install vLLM (Method 1: Docker recommended)
docker pull vllm/vllm-openai:latest

# 3. Start vLLM
docker run --gpus all -p 8001:8000 --ipc=host \
    vllm/vllm-openai:latest \
    --model mistralai/Mistral-7B-Instruct-v0.2 \
    --host 0.0.0.0 --port 8000

# 4. Test vLLM
curl http://localhost:8001/v1/models

# 5. Switch provider
sed -i 's/LLM_PROVIDER=ollama/LLM_PROVIDER=vllm/' webapp/backend/.env

# 6. Restart backend
cd webapp/backend
pkill -f "uvicorn main:app"
python -m uvicorn main:app --reload

# 7. Test through UI
# Open http://localhost:3000 and send a message

# 8. Rollback if needed
sed -i 's/LLM_PROVIDER=vllm/LLM_PROVIDER=ollama/' webapp/backend/.env
```

---

## Getting Help

If issues persist:

1. **Check logs**:
   - vLLM: `logs/vllm_*.log`
   - Backend: Backend console output

2. **Search existing issues**:
   - vLLM GitHub: https://github.com/vllm-project/vllm/issues
   - RAG System: [GitHub Issues](../../issues)

3. **Create detailed bug report** with:
   - System info (`nvidia-smi`, `python --version`)
   - vLLM version (`pip show vllm`)
   - Complete error message
   - Steps to reproduce
   - Logs

4. **Community support**:
   - vLLM Discord: https://discord.gg/vllm
   - vLLM Discussions: https://github.com/vllm-project/vllm/discussions

---

## Quick Reference

### Restart Everything

```bash
# Kill all vLLM processes
pkill -9 -f vllm

# Kill backend
pkill -9 -f "uvicorn main:app"

# Clear cache
rm -rf /tmp/ray/*

# Restart vLLM
./scripts/setup_vllm.sh mistralai/Mistral-7B-Instruct-v0.2 1 1

# Restart backend
cd webapp/backend
python -m uvicorn main:app --reload
```

### Check Status

```bash
# vLLM running?
ps aux | grep vllm
lsof -i :8001

# GPU usage
nvidia-smi

# Test API
curl http://localhost:8001/v1/models

# Backend provider
grep LLM_PROVIDER webapp/backend/.env
```

### Switch Back to Ollama

```bash
# Update config
sed -i 's/LLM_PROVIDER=vllm/LLM_PROVIDER=ollama/' webapp/backend/.env

# Restart backend
cd webapp/backend
pkill -f "uvicorn main:app"
python -m uvicorn main:app --reload

# No need to stop vLLM (won't be used)
```

---

**Still having issues?** See [VLLM_COMPLETE_GUIDE.md](VLLM_COMPLETE_GUIDE.md) for comprehensive documentation.
