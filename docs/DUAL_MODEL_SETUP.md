# Dual Model Strategy - GPU Optimization Guide

## Overview

The Dual Model Strategy significantly improves video generation performance by using two different Ollama models:
- **Large model** (e.g., `gemma4:e4b` - 9.6GB) for high-quality script generation
- **Small model** (e.g., `gemma:2b` - 1.4GB) for fast keyword generation

This approach provides **47.5% faster LLM processing** while maintaining excellent content quality.

## Performance Gains

| Task | Before (Single Model) | After (Dual Model) | Improvement |
|------|----------------------|-------------------|-------------|
| **Script Generation** | 80s (gemma4:e4b) | 80s (gemma4:e4b) | Unchanged (quality priority) |
| **Keyword Generation** | 80s (gemma4:e4b) | 4.3s (gemma:2b) | **94.6% faster** |
| **Total LLM Time** | ~160s | ~84s | **47.5% faster** |

## Prerequisites

- Ollama installed and accessible
- At least 11GB VRAM for both models (9.6GB + 1.4GB)
- Docker setup with MoneyPrinterTurbo

## Installation Steps

### 1. Download the Small Model

```bash
# Download gemma:2b model to Ollama
docker exec ollama ollama pull gemma:2b
```

### 2. Update Configuration

Edit your `config.toml` file:

```toml
[app]
llm_provider = "ollama"

# Ollama Settings
ollama_base_url = "http://ollama:11434/v1"

# Primary model for script generation (quality matters)
ollama_model_name = "gemma4:e4b"

# Secondary model for keyword generation (speed matters)
ollama_keyword_model = "gemma:2b"
ollama_use_keyword_model = true

ollama_keep_alive_minutes = 2
ollama_unload_after_generate = true
```

**Configuration Parameters:**

- `ollama_model_name`: Primary model for script generation (high quality)
- `ollama_keyword_model`: Secondary model for keyword generation (high speed)
- `ollama_use_keyword_model`: Set to `true` to enable dual model feature

### 3. Restart the API Container

```bash
docker restart moneyprinterturbo-dev-api
```

### 4. Verify Configuration

```bash
# Check that configuration loaded correctly
docker exec moneyprinterturbo-dev-api python3 -c "from app.config import config; print('Primary:', config.app.get('ollama_model_name')); print('Keyword:', config.app.get('ollama_keyword_model')); print('Enabled:', config.app.get('ollama_use_keyword_model'))"
```

Expected output:
```
Primary: gemma4:e4b
Keyword: gemma:2b
Enabled: True
```

## How It Works

The system automatically routes LLM requests to the appropriate model based on task type:

1. **Script Generation** → Uses `ollama_model_name` (large model)
   - Prioritizes quality and coherence
   - Longer generation time acceptable

2. **Keyword Generation** → Uses `ollama_keyword_model` (small model)
   - Prioritizes speed
   - Quality remains excellent for simple keyword tasks

3. **Model Selection Logic** (in `app/services/llm.py`):
   ```python
   def _get_ollama_model(task_type: str = "general") -> str:
       if task_type == "keywords" and ollama_use_keyword_model:
           return ollama_keyword_model
       return ollama_model_name  # Default to primary model
   ```

## Testing

### Test Keyword Generation

```bash
curl -X POST http://localhost:8089/api/v1/terms \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: your-api-key" \
  -d '{
    "video_subject": "home improvement",
    "video_script": "Transform your kitchen with modern appliances.",
    "amount": 3
  }'
```

Check the logs to confirm `gemma:2b` is used:
```bash
docker logs --tail 50 moneyprinterturbo-dev-api | grep "Using keyword model"
```

Expected output:
```
DEBUG | _get_ollama_model - Using keyword model: gemma:2b
```

### Test Script Generation

```bash
curl -X POST http://localhost:8089/api/v1/scripts \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: your-api-key" \
  -d '{
    "video_subject": "home improvement tips",
    "video_language": "en",
    "paragraph_number": 1
  }'
```

Check the logs to confirm `gemma4:e4b` is used:
```bash
docker logs --tail 50 moneyprinterturbo-dev-api | grep "Using primary model"
```

Expected output:
```
DEBUG | _get_ollama_model - Using primary model: gemma4:e4b
```

## Model Recommendations

### Small Models (Keyword Generation)

| Model | Size | Speed | Quality | Recommendation |
|-------|------|-------|---------|----------------|
| `gemma:2b` | 1.4GB | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | **Recommended** |
| `phi3:mini` | 2.3GB | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Good alternative |
| `tinyllama` | 0.6GB | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Ultra-fast but lower quality |

### Large Models (Script Generation)

| Model | Size | Speed | Quality | Recommendation |
|-------|------|-------|---------|----------------|
| `gemma4:e4b` | 9.6GB | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **Recommended** |
| `llama3:8b` | 4.7GB | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Good balance |
| `mistral:7b` | 4.1GB | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Faster alternative |

## Troubleshooting

### Models Not Switching

**Symptom:** Both tasks use the same model

**Solutions:**
1. Verify `ollama_use_keyword_model = true` in config
2. Restart the API container
3. Check logs for model selection: `docker logs moneyprinterturbo-dev-api | grep "get_ollama_model"`

### Out of VRAM

**Symptom:** Model loading fails or system becomes slow

**Solutions:**
1. Use smaller models (e.g., `phi3:mini` instead of `gemma:2b`)
2. Reduce `ollama_keep_alive_minutes` to unload models faster
3. Set `ollama_unload_after_generate = true` to free VRAM immediately
4. Ensure only one model is in VRAM at a time

### Keyword Quality Issues

**Symptom:** Keywords are not relevant or useful

**Solutions:**
1. Test different small models (see recommendations above)
2. Increase model size (e.g., use `phi3:mini` 2.3GB instead of `gemma:2b` 1.4GB)
3. Fall back to single model by setting `ollama_use_keyword_model = false`

### Performance Not Improved

**Symptom:** Generation times are still slow

**Solutions:**
1. Verify models are pre-loaded: `docker exec ollama ollama list`
2. Check GPU utilization: `nvidia-smi`
3. Review logs for model warmup delays
4. Ensure `ollama_keep_alive_minutes` is set appropriately (default: 2)

## Rollback Procedure

If you encounter issues and need to revert to single-model operation:

### Quick Rollback

Edit `config.toml`:
```toml
# Disable dual model feature
ollama_use_keyword_model = false
```

Restart the container:
```bash
docker restart moneyprinterturbo-dev-api
```

### Complete Rollback

If you want to remove the dual model code entirely:

```bash
cd /mnt/data/repos/MoneyPrinterTurbo-openai-tts
git stash  # Save any other changes
git checkout <commit-before-dual-model>  # Use git tag or commit hash
docker restart moneyprinterturbo-dev-api
```

## Advanced Configuration

### Different Model Combinations

You can mix and match any Ollama models:

```toml
# Fast script + ultra-fast keywords
ollama_model_name = "llama3:8b"          # 4.7GB
ollama_keyword_model = "tinyllama"       # 0.6GB

# High quality script + balanced keywords  
ollama_model_name = "gemma4:e4b"         # 9.6GB
ollama_keyword_model = "phi3:mini"       # 2.3GB

# Balanced approach
ollama_model_name = "mistral:7b"         # 4.1GB
ollama_keyword_model = "gemma:2b"        # 1.4GB
```

### Memory Management

```toml
# Aggressive memory management (unload immediately)
ollama_keep_alive_minutes = 0
ollama_unload_after_generate = true

# Keep models warm (recommended for frequent generation)
ollama_keep_alive_minutes = 5
ollama_unload_after_generate = false

# Keep models forever (maximum speed, high VRAM usage)
ollama_keep_alive_minutes = -1
ollama_unload_after_generate = false
```

## Monitoring

### Check Current Models in VRAM

```bash
docker exec ollama ollama ps
```

### Monitor GPU Usage

```bash
watch -n 1 nvidia-smi
```

### View Model Selection Logs

```bash
docker logs -f moneyprinterturbo-dev-api | grep -E "Using (primary|keyword) model|Profile.*took"
```

## Additional Optimizations

### AllTalk TTS GPU Acceleration

AllTalk TTS is already configured for GPU acceleration in the docker compose file:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

Verify GPU access:
```bash
docker exec alltalk nvidia-smi
```

### Combined Performance Impact

With both optimizations:
- **LLM Processing:** 47.5% faster (dual model)
- **TTS Generation:** GPU-accelerated (already enabled)
- **Overall Workflow:** Significantly smoother and more responsive

## Support

For issues or questions:
1. Check logs: `docker logs moneyprinterturbo-dev-api`
2. Review this guide's troubleshooting section
3. File an issue on the project repository

## Credits

- **gemma** models by Google
- **Ollama** for model serving
- **MoneyPrinterTurbo** community for testing and feedback
