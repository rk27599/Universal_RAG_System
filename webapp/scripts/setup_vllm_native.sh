#!/bin/bash

# ==============================================================================
# vLLM Setup Script for RAG System
# ==============================================================================
# This script helps start vLLM server with optimal multi-GPU configuration
#
# Usage:
#   ./setup_vllm.sh [model_name] [gpu_count] [tensor_parallel_size]
#
# Examples:
#   ./setup_vllm.sh mistralai/Mistral-7B-Instruct-v0.2 1 1
#   ./setup_vllm.sh meta-llama/Llama-2-13b-chat-hf 2 2
#   ./setup_vllm.sh codellama/CodeLlama-34b-Instruct-hf 4 4
# ==============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
DEFAULT_MODEL="mistralai/Mistral-7B-Instruct-v0.2"
DEFAULT_GPU_COUNT=1
DEFAULT_TENSOR_PARALLEL=1
DEFAULT_PORT=8001
DEFAULT_HOST="localhost"

# Get parameters or use defaults
MODEL_NAME="${1:-$DEFAULT_MODEL}"
GPU_COUNT="${2:-$DEFAULT_GPU_COUNT}"
TENSOR_PARALLEL="${3:-$DEFAULT_TENSOR_PARALLEL}"
VLLM_PORT="${4:-$DEFAULT_PORT}"
VLLM_HOST="${5:-$DEFAULT_HOST}"

echo -e "${BLUE}==============================================================================
vLLM Setup for RAG System
==============================================================================${NC}"

echo -e "\n${YELLOW}Configuration:${NC}"
echo "  Model: $MODEL_NAME"
echo "  GPU Count: $GPU_COUNT"
echo "  Tensor Parallel Size: $TENSOR_PARALLEL"
echo "  Port: $VLLM_PORT"
echo "  Host: $VLLM_HOST"

# Check if vLLM is installed
echo -e "\n${BLUE}[1/5] Checking vLLM installation...${NC}"
if ! python -c "import vllm" 2>/dev/null; then
    echo -e "${RED}❌ vLLM is not installed!${NC}"
    echo -e "${YELLOW}Please install vLLM first:${NC}"
    echo "  pip install vllm"
    exit 1
else
    VLLM_VERSION=$(python -c "import vllm; print(vllm.__version__)")
    echo -e "${GREEN}✅ vLLM version $VLLM_VERSION is installed${NC}"
fi

# Check GPU availability
echo -e "\n${BLUE}[2/5] Checking GPU availability...${NC}"
if ! nvidia-smi &>/dev/null; then
    echo -e "${RED}❌ nvidia-smi not found or no GPUs detected!${NC}"
    echo -e "${YELLOW}vLLM requires CUDA-capable GPUs${NC}"
    exit 1
fi

AVAILABLE_GPUS=$(nvidia-smi --query-gpu=name --format=csv,noheader | wc -l)
echo -e "${GREEN}✅ Found $AVAILABLE_GPUS GPU(s)${NC}"
nvidia-smi --query-gpu=index,name,memory.total --format=csv,noheader

if [ "$GPU_COUNT" -gt "$AVAILABLE_GPUS" ]; then
    echo -e "${RED}❌ Requested $GPU_COUNT GPUs but only $AVAILABLE_GPUS available!${NC}"
    exit 1
fi

# Validate tensor parallel size
echo -e "\n${BLUE}[3/5] Validating tensor parallelism configuration...${NC}"
if [ $((GPU_COUNT % TENSOR_PARALLEL)) -ne 0 ]; then
    echo -e "${RED}❌ Tensor parallel size ($TENSOR_PARALLEL) must evenly divide GPU count ($GPU_COUNT)!${NC}"
    echo -e "${YELLOW}Valid options for $GPU_COUNT GPU(s):${NC}"
    for i in $(seq 1 $GPU_COUNT); do
        if [ $((GPU_COUNT % i)) -eq 0 ]; then
            echo "  - Tensor parallel size: $i"
        fi
    done
    exit 1
fi
echo -e "${GREEN}✅ Tensor parallelism configuration is valid${NC}"

# Check if port is available
echo -e "\n${BLUE}[4/5] Checking if port $VLLM_PORT is available...${NC}"
if lsof -Pi :$VLLM_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Port $VLLM_PORT is already in use!${NC}"
    echo -e "${YELLOW}   Another vLLM instance might be running${NC}"
    read -p "   Stop existing service and continue? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        PID=$(lsof -Pi :$VLLM_PORT -sTCP:LISTEN -t)
        echo "   Stopping process $PID..."
        kill -9 $PID 2>/dev/null || true
        sleep 2
    else
        echo -e "${RED}❌ Cannot start vLLM - port in use${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}✅ Port $VLLM_PORT is available${NC}"

# Start vLLM server
echo -e "\n${BLUE}[5/5] Starting vLLM server...${NC}"
echo -e "${YELLOW}This may take several minutes on first run (model download/loading)${NC}"

# Build vLLM command with optimized settings
VLLM_CMD="python -m vllm.entrypoints.openai.api_server \
    --model $MODEL_NAME \
    --host $VLLM_HOST \
    --port $VLLM_PORT \
    --tensor-parallel-size $TENSOR_PARALLEL"

# Add GPU-specific optimizations
if [ "$GPU_COUNT" -gt 1 ]; then
    VLLM_CMD="$VLLM_CMD --distributed-executor-backend ray"
fi

# Display full command
echo -e "\n${YELLOW}Starting with command:${NC}"
echo "$VLLM_CMD"
echo ""

# Create logs directory
mkdir -p logs

# Start vLLM in background
LOG_FILE="logs/vllm_$(date +%Y%m%d_%H%M%S).log"
echo -e "${YELLOW}Logs will be written to: $LOG_FILE${NC}"

# Start vLLM and capture PID
nohup $VLLM_CMD > "$LOG_FILE" 2>&1 &
VLLM_PID=$!

echo -e "${GREEN}✅ vLLM server started (PID: $VLLM_PID)${NC}"
echo ""

# Wait for server to be ready
echo -e "${YELLOW}Waiting for vLLM server to be ready...${NC}"
MAX_RETRIES=60
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://$VLLM_HOST:$VLLM_PORT/v1/models >/dev/null 2>&1; then
        echo -e "${GREEN}✅ vLLM server is ready!${NC}"
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo -n "."
    sleep 2

    # Check if process is still running
    if ! kill -0 $VLLM_PID 2>/dev/null; then
        echo -e "\n${RED}❌ vLLM process died unexpectedly!${NC}"
        echo -e "${YELLOW}Check logs: $LOG_FILE${NC}"
        tail -n 50 "$LOG_FILE"
        exit 1
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "\n${RED}❌ vLLM server failed to start within expected time${NC}"
    echo -e "${YELLOW}Check logs: $LOG_FILE${NC}"
    tail -n 50 "$LOG_FILE"
    exit 1
fi

# Display server information
echo -e "\n${GREEN}==============================================================================
vLLM Server Successfully Started!
==============================================================================${NC}"

echo -e "\n${YELLOW}Server Details:${NC}"
echo "  Endpoint: http://$VLLM_HOST:$VLLM_PORT"
echo "  Model: $MODEL_NAME"
echo "  GPUs: $GPU_COUNT"
echo "  Tensor Parallel: $TENSOR_PARALLEL"
echo "  PID: $VLLM_PID"
echo "  Logs: $LOG_FILE"

echo -e "\n${YELLOW}API Endpoints:${NC}"
echo "  Models: http://$VLLM_HOST:$VLLM_PORT/v1/models"
echo "  Chat: http://$VLLM_HOST:$VLLM_PORT/v1/chat/completions"
echo "  Completions: http://$VLLM_HOST:$VLLM_PORT/v1/completions"

echo -e "\n${YELLOW}Update your .env file:${NC}"
echo "  LLM_PROVIDER=vllm"
echo "  VLLM_BASE_URL=http://$VLLM_HOST:$VLLM_PORT"
echo "  VLLM_GPU_COUNT=$GPU_COUNT"
echo "  VLLM_TENSOR_PARALLEL_SIZE=$TENSOR_PARALLEL"

echo -e "\n${YELLOW}Management Commands:${NC}"
echo "  Check status: curl http://$VLLM_HOST:$VLLM_PORT/v1/models"
echo "  View logs: tail -f $LOG_FILE"
echo "  Stop server: kill $VLLM_PID"

echo -e "\n${GREEN}✅ Ready to process requests!${NC}"
echo -e "   Restart your backend to use vLLM provider\n"
