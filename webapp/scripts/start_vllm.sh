#!/bin/bash
# vLLM Startup Script - Production Ready Configuration
# Supports Qwen3-4B-Thinking-2507-FP8 with optimized settings for 8GB GPU

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration (tested and working)
MODEL="Qwen/Qwen3-4B-Thinking-2507-FP8"
CONTEXT_WINDOW=16384
GPU_MEMORY_UTIL=0.95
MAX_NUM_SEQS=1
CONTAINER_NAME="vllm-server"
PORT=8001

print_header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  vLLM Server Management${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        echo "Install Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi

    if ! docker ps &> /dev/null; then
        print_error "Docker daemon is not running or you don't have permission"
        echo "Try: sudo systemctl start docker"
        echo "Or add yourself to docker group: sudo usermod -aG docker \$USER"
        exit 1
    fi

    print_status "Docker is available"
}

stop_existing_container() {
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        print_info "Stopping existing vLLM container..."
        docker stop "${CONTAINER_NAME}" 2>/dev/null || true
        docker rm "${CONTAINER_NAME}" 2>/dev/null || true
        print_status "Existing container removed"
    fi
}

start_vllm() {
    local model=$1
    local context=$2
    local gpu_util=$3
    local max_seqs=$4

    print_info "Starting vLLM with configuration:"
    echo "  Model: ${model}"
    echo "  Context Window: ${context} tokens"
    echo "  GPU Memory Util: ${gpu_util}"
    echo "  Max Concurrent Seqs: ${max_seqs}"
    echo "  Port: ${PORT}"
    echo ""

    docker run -d \
        --name "${CONTAINER_NAME}" \
        --gpus all \
        -p ${PORT}:8000 \
        --ipc=host \
        -e VLLM_USE_V1=0 \
        -v $HOME/.cache/huggingface:/root/.cache/huggingface \
        vllm/vllm-openai:v0.10.1.1 \
        --model "${model}" \
        --dtype float16 \
        --kv-cache-dtype fp8 \
        --gpu-memory-utilization "${gpu_util}" \
        --max-model-len "${context}" \
        --max-num-seqs "${max_seqs}" \
        --disable-log-requests

    if [ $? -eq 0 ]; then
        print_status "vLLM container started successfully"
    else
        print_error "Failed to start vLLM container"
        exit 1
    fi
}

wait_for_vllm() {
    print_info "Waiting for vLLM to be ready..."
    echo "This may take 1-3 minutes (downloading model on first run)"
    echo ""

    local max_attempts=60
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:${PORT}/v1/models >/dev/null 2>&1; then
            print_status "vLLM is ready!"
            return 0
        fi

        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done

    echo ""
    print_error "vLLM failed to start within 120 seconds"
    print_info "Check logs: docker logs ${CONTAINER_NAME}"
    return 1
}

show_model_info() {
    print_info "Model Information:"
    curl -s http://localhost:${PORT}/v1/models | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    model = data['data'][0]
    print(f\"  Model ID: {model['id']}\")
    print(f\"  Max Context: {model['max_model_len']:,} tokens\")
except:
    print('  Unable to retrieve model info')
" || echo "  Unable to retrieve model info"
}

test_vllm() {
    print_info "Testing vLLM with sample query..."

    response=$(curl -s http://localhost:${PORT}/v1/chat/completions \
        -H "Content-Type: application/json" \
        -d '{
            "model":"'${MODEL}'",
            "messages":[{"role":"user","content":"Say hello in 5 words"}],
            "max_tokens":20
        }' | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data['choices'][0]['message']['content'][:80])
except Exception as e:
    print(f'Error: {e}')
")

    if [ -n "$response" ] && [[ ! "$response" =~ ^Error ]]; then
        print_status "Test successful!"
        echo "  Response: ${response}"
    else
        print_error "Test failed"
        echo "  Response: ${response}"
    fi
}

show_status() {
    print_header
    echo ""

    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        print_status "vLLM container is running"
        echo ""
        docker ps --filter "name=${CONTAINER_NAME}" --format "table {{.Image}}\t{{.Status}}\t{{.Ports}}"
        echo ""

        if curl -s http://localhost:${PORT}/v1/models >/dev/null 2>&1; then
            print_status "vLLM API is responding"
            show_model_info
        else
            print_warning "vLLM container is running but API is not ready yet"
            print_info "Check logs: docker logs ${CONTAINER_NAME}"
        fi
    else
        print_info "vLLM container is not running"
        echo ""
        echo "Start vLLM: bash start_vllm.sh"
    fi
    echo ""
}

show_logs() {
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        docker logs -f "${CONTAINER_NAME}"
    else
        print_error "vLLM container is not running"
    fi
}

show_menu() {
    print_header
    echo ""
    echo "1) Start vLLM (Default: Qwen3-4B-FP8, 16K context)"
    echo "2) Start vLLM (32K context - requires more VRAM)"
    echo "3) Check Status"
    echo "4) View Logs"
    echo "5) Stop vLLM"
    echo "6) Restart vLLM"
    echo "7) Exit"
    echo ""
    read -p "Select option [1-7]: " choice

    case $choice in
        1)
            check_docker
            stop_existing_container
            start_vllm "${MODEL}" 16384 0.95 1
            if wait_for_vllm; then
                echo ""
                show_model_info
                echo ""
                test_vllm
                echo ""
                print_status "vLLM is ready to use!"
                print_info "Backend config: LLM_PROVIDER=vllm in webapp/backend/.env"
            fi
            ;;
        2)
            check_docker
            stop_existing_container
            print_warning "32K context requires ~7-8GB VRAM"
            read -p "Continue? (y/n): " confirm
            if [[ $confirm == "y" ]]; then
                start_vllm "${MODEL}" 32768 0.90 1
                if wait_for_vllm; then
                    echo ""
                    show_model_info
                    echo ""
                    test_vllm
                fi
            fi
            ;;
        3)
            show_status
            ;;
        4)
            show_logs
            ;;
        5)
            stop_existing_container
            print_status "vLLM stopped"
            ;;
        6)
            stop_existing_container
            sleep 1
            start_vllm "${MODEL}" 16384 0.95 1
            wait_for_vllm
            ;;
        7)
            exit 0
            ;;
        *)
            print_error "Invalid option"
            ;;
    esac
}

# Main execution
if [ $# -eq 0 ]; then
    # Interactive mode
    show_menu
else
    # Command line mode
    case "$1" in
        start)
            check_docker
            stop_existing_container
            start_vllm "${MODEL}" 16384 0.95 1
            wait_for_vllm
            ;;
        stop)
            stop_existing_container
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        restart)
            stop_existing_container
            sleep 1
            start_vllm "${MODEL}" 16384 0.95 1
            wait_for_vllm
            ;;
        *)
            echo "Usage: $0 {start|stop|status|logs|restart}"
            echo "Or run without arguments for interactive menu"
            exit 1
            ;;
    esac
fi
