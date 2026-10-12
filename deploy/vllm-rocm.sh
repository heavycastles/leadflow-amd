#!/usr/bin/env bash
# Run on an AMD Developer Cloud MI300X droplet (ROCm preinstalled). Serves an OpenAI-compatible API on :8000.
set -euo pipefail
MODEL="${LLM_MODEL:-Qwen/Qwen2.5-7B-Instruct}"
rocm-smi || true
docker run -d --name vllm --restart unless-stopped \
  --device=/dev/kfd --device=/dev/dri --group-add video --ipc=host --shm-size 16g \
  --security-opt seccomp=unconfined \
  -e HF_TOKEN="${HF_TOKEN:-}" -v hf_cache:/root/.cache/huggingface -p 8000:8000 \
  rocm/vllm:latest vllm serve "$MODEL" --host 0.0.0.0 --port 8000 --max-model-len 8192 \
  ${VLLM_API_KEY:+--api-key "$VLLM_API_KEY"}
echo "waiting for vLLM..."; until curl -sf localhost:8000/v1/models >/dev/null; do sleep 5; done
curl -s localhost:8000/v1/models
echo; echo "Set on the app: LLM_BACKEND=openai LLM_BASE_URL=http://<droplet-ip>:8000/v1 LLM_MODEL=$MODEL"
