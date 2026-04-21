# Implementation Plan: Dual Model Strategy (Option A)
**MoneyPrinterTurbo GPU Optimization**

**Goal**: Implement dual model strategy with GPU-accelerated TTS  
**Expected Improvement**: 36% faster (330s → 210s per video)  
**Estimated Time**: 6-8 hours

---

## Phase 1: Test Small Model Quality ⏱️ 30 min

### Objective
Verify that gemma:2b produces acceptable keyword quality before implementing full dual model support.

### Steps

1. **Download gemma:2b model**
   ```bash
   docker exec ollama ollama pull gemma:2b
   ```

2. **Run quality test script**
   ```bash
   cd /mnt/data/repos/MoneyPrinterTurbo-openai-tts/docs
   chmod +x test_small_model.sh
   ./test_small_model.sh
   ```

3. **Manual quality test via API**
   ```bash
   # Test with large model
   curl -X POST http://192.168.0.116:8089/api/v1/terms \
     -H "Content-Type: application/json" \
     -d '{
       "video_subject": "home renovation",
       "video_script": "Transform your kitchen with modern appliances and custom cabinets. Learn professional techniques for tiling and painting.",
       "amount": 5
     }'
   
   # Compare results - are keywords relevant?
   ```

4. **Check model sizes**
   ```bash
   docker exec ollama ollama list
   # Verify gemma:2b is ~1.4GB
   ```

### Success Criteria
- ✅ gemma:2b generates relevant keywords
- ✅ Keywords are similar quality to gemma4:e4b
- ✅ Generation time is significantly faster (15-20s vs 30s+)

### Decision Point
**PROCEED** if keywords are acceptable  
**STOP** if quality is poor - stick with single model

---

## Phase 2: Add Dual Model Configuration ⏱️ 30 min

### Objective
Add configuration options for dual model support with feature flag.

### Steps

1. **Update config.toml**
   ```bash
   # Edit /mnt/data/repos/MoneyPrinterTurbo-openai-tts/config.toml
   ```

   Add these settings:
   ```toml
   [app]
   llm_provider = "ollama"
   
   # Primary model for script generation (quality)
   ollama_model_name = "gemma4:e4b"
   
   # Secondary model for keyword generation (speed)
   ollama_keyword_model = "gemma:2b"
   ollama_use_keyword_model = true  # Feature flag
   
   # Model management
   ollama_base_url = "http://ollama:11434/v1"
   ollama_keep_alive_minutes = 5
   ollama_unload_after_generate = true
   ```

2. **Update config.example.toml** (for documentation)
   ```bash
   # Add the same settings to config.example.toml with comments
   ```

3. **Verify config loads**
   ```bash
   docker exec moneyprinterturbo-dev-api python3 -c "from app.config import config; print(config.app.get('ollama_keyword_model'))"
   # Should print: gemma:2b
   ```

### Success Criteria
- ✅ Config file updated
- ✅ Settings load correctly
- ✅ Feature flag accessible

---

## Phase 3: Implement Model Routing Logic ⏱️ 2 hours

### Objective
Update llm.py to select appropriate model based on task type.

### Code Changes

**File: `/mnt/data/repos/MoneyPrinterTurbo-openai-tts/app/services/llm.py`**

1. **Add helper function to select model**

   Insert after `unload_ollama_model()` function (~line 110):
   ```python
   def _get_ollama_model(task_type: str = "general") -> str:
       """
       Get the appropriate Ollama model based on task type.
       
       Args:
           task_type: "script", "keywords", or "general"
           
       Returns:
           Model name to use
       """
       if config.app.get("llm_provider", "openai") != "ollama":
           return ""
       
       # Check if dual model feature is enabled
       use_keyword_model = config.app.get("ollama_use_keyword_model", False)
       
       if task_type == "keywords" and use_keyword_model:
           keyword_model = config.app.get("ollama_keyword_model", "")
           if keyword_model:
               logger.debug(f"Using keyword model: {keyword_model}")
               return keyword_model
       
       # Default to primary model
       primary_model = config.app.get("ollama_model_name", "")
       logger.debug(f"Using primary model: {primary_model}")
       return primary_model
   ```

2. **Update `_generate_response()` to accept task_type**

   Find `_generate_response()` function (~line 355):
   ```python
   def _generate_response(prompt: str, task_type: str = "general") -> str:
       """
       Generate response using configured LLM provider.
       
       Args:
           prompt: The prompt to send
           task_type: Type of task - "script", "keywords", or "general"
       """
   ```

3. **Update Ollama client initialization in `_generate_response()`**

   Find the Ollama section (~line 395):
   ```python
   elif llm_provider == "ollama":
       logger.debug("LLM provider: ollama")
       base_url = config.app.get("ollama_base_url", "http://localhost:11434/v1")
       if not base_url:
           base_url = "http://localhost:11434/v1"
       
       # Get appropriate model based on task type
       model_name = _get_ollama_model(task_type)
       if not model_name:
           model_name = config.app.get("ollama_model_name", "")
       
       # Warmup check - use the selected model
       if not check_ollama_model_loaded(model_name):
           logger.info(f"Model {model_name} not loaded, warming up...")
           warmup_ollama_model(model_name)
       
       client = OpenAI(base_url=base_url, api_key="ollama")
       response = client.chat.completions.create(
           model=model_name,  # Use selected model
           messages=[{"role": "user", "content": prompt}],
       )
   ```

4. **Update `generate_script()` to pass task_type**

   Find `generate_script()` function (~line 440):
   ```python
   def generate_script(
       video_subject: str, language: str = "", paragraph_number: int = 1, skip_unload: bool = False
   ) -> str:
       # ... existing code ...
       
       for i in range(_max_retries + 1):
           try:
               # Pass task_type="script"
               final_script = _generate_response(prompt, task_type="script")
               if final_script and "Error: " not in final_script:
                   break
   ```

5. **Update `generate_terms()` to pass task_type**

   Find `generate_terms()` function (~line 530):
   ```python
   def generate_terms(
       video_subject: str, video_script: str, amount: int = 5, skip_unload: bool = False
   ) -> List[str]:
       # ... existing code ...
       
       for i in range(_max_retries + 1):
           try:
               # Pass task_type="keywords"
               response = _generate_response(prompt, task_type="keywords")
               logger.debug(f"Response: {response}")
   ```

6. **Update unload calls to use correct model**

   In `generate_script()` finally block:
   ```python
   finally:
       if not skip_unload and config.app.get("llm_provider", "openai") == "ollama":
           model_name = _get_ollama_model("script")
           unload_ollama_model(model_name)
   ```

   In `generate_terms()` finally block:
   ```python
   finally:
       if not skip_unload and config.app.get("llm_provider", "openai") == "ollama":
           model_name = _get_ollama_model("keywords")
           unload_ollama_model(model_name)
   ```

### Testing Phase 3

```bash
# Restart API
cd /mnt/samsungssd/docker
sudo docker compose restart moneyprinterturbo-dev-api

# Watch logs
sudo docker logs -f moneyprinterturbo-dev-api

# Test script generation (should use gemma4:e4b)
curl -X POST http://192.168.0.116:8089/api/v1/scripts \
  -H "Content-Type: application/json" \
  -d '{
    "video_subject": "test subject",
    "video_language": "en",
    "paragraph_number": 1
  }'

# Test keyword generation (should use gemma:2b)
curl -X POST http://192.168.0.116:8089/api/v1/terms \
  -H "Content-Type: application/json" \
  -d '{
    "video_subject": "test",
    "video_script": "test script",
    "amount": 5
  }'

# Check logs for "Using keyword model: gemma:2b"
```

### Success Criteria
- ✅ Script generation uses gemma4:e4b
- ✅ Keyword generation uses gemma:2b
- ✅ Logs show correct model selection
- ✅ API endpoints return valid responses

---

## Phase 4: Update API Endpoints ⏱️ 30 min

### Objective
Ensure API endpoints properly utilize the dual model system.

### Verification Only

The changes in Phase 3 should automatically apply to API endpoints since they call the updated `llm.generate_script()` and `llm.generate_terms()` functions.

**File: `/mnt/data/repos/MoneyPrinterTurbo-openai-tts/app/controllers/v1/llm.py`**

Current code already correct:
```python
def generate_video_script(request: Request, body: VideoScriptRequest):
    video_script = llm.generate_script(  # Will use gemma4:e4b
        video_subject=body.video_subject,
        language=body.video_language,
        paragraph_number=body.paragraph_number,
        skip_unload=True,
    )

def generate_video_terms(request: Request, body: VideoTermsRequest):
    video_terms = llm.generate_terms(  # Will use gemma:2b
        video_subject=body.video_subject,
        video_script=body.video_script,
        amount=body.amount,
        skip_unload=True,
    )
```

### Testing

```bash
# Test via WebUI
# 1. Open http://192.168.0.116:8502
# 2. Generate a script
# 3. Generate keywords
# 4. Watch API logs for model usage

# Should see:
# "Using primary model: gemma4:e4b" for script
# "Using keyword model: gemma:2b" for keywords
```

### Success Criteria
- ✅ WebUI script generation works
- ✅ WebUI keyword generation works
- ✅ Correct models used for each task

---

## Phase 5: Configure AllTalk GPU Acceleration ⏱️ 1 hour

### Objective
Enable GPU acceleration for AllTalk TTS to utilize freed VRAM.

### Steps

1. **Update AllTalk compose file**

   **File: `/mnt/samsungssd/docker/compose/mark-B550-GAMING-X/alltalk.yml`**

   ```yaml
   services:
     alltalk:
       image: erew123/alltalk_tts:latest
       container_name: alltalk
       restart: unless-stopped
       ports:
         - "7851:7851"
       environment:
         - TZ=${TZ}
         - PUID=${PUID}
         - PGID=${PGID}
       volumes:
         - $DOCKERDIR/appdata/alltalk:/app/alltalk_tts/config
         - $DOCKERDIR/appdata/alltalk/models:/app/alltalk_tts/models
       networks:
         - default
       deploy:
         resources:
           reservations:
             devices:
               - driver: nvidia
                 count: 1
                 capabilities: [gpu]
   ```

2. **Restart AllTalk**
   ```bash
   cd /mnt/samsungssd/docker
   sudo docker compose stop alltalk
   sudo docker compose up -d alltalk
   
   # Verify GPU access
   sudo docker exec alltalk nvidia-smi
   ```

3. **Configure AllTalk to use GPU**
   
   Access AllTalk UI: `http://192.168.0.116:7851`
   
   - Go to Settings
   - Enable GPU acceleration
   - Select XTTS model (GPU-optimized)
   - Save settings

4. **Update MoneyPrinterTurbo to use AllTalk**

   If not already configured, update config.toml:
   ```toml
   [voice]
   provider = "alltalk"  # or edge if preferred
   alltalk_base_url = "http://alltalk:7851"
   ```

### Testing Phase 5

```bash
# Test TTS directly
curl -X POST http://192.168.0.116:7851/api/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is a test of GPU accelerated text to speech.",
    "voice": "default"
  }'

# Monitor GPU usage
watch -n 1 nvidia-smi

# Should see alltalk using GPU memory during generation
```

### Success Criteria
- ✅ AllTalk has GPU access
- ✅ TTS generation uses GPU
- ✅ Audio quality is good
- ✅ Speed is improved (20s vs 60s)

---

## Phase 6: End-to-End Testing ⏱️ 2 hours

### Objective
Test complete workflow and measure actual performance improvements.

### Test Scenarios

#### Test 1: Simple Video (Baseline)

```bash
# Record start time
START_TIME=$(date +%s)

# Create video via WebUI:
# 1. Subject: "home improvement tips"
# 2. Generate script (watch for gemma4:e4b in logs)
# 3. Generate keywords (watch for gemma:2b in logs)
# 4. Generate 3 sentence keywords
# 5. Create video task

# Record end time when video completes
END_TIME=$(date +%s)
TOTAL_TIME=$((END_TIME - START_TIME))
echo "Total time: ${TOTAL_TIME} seconds"

# Expected: ~210 seconds (vs 330 before)
```

#### Test 2: Monitor Model Usage

```bash
# In one terminal: Watch API logs
sudo docker logs -f moneyprinterturbo-dev-api | grep -E "Using (primary|keyword) model|Model.*loaded"

# In another: Watch GPU
watch -n 1 nvidia-smi

# Create a video and observe:
# 1. gemma4:e4b loads for script
# 2. gemma:2b loads for keywords (should be much faster)
# 3. GPU used by AllTalk during TTS
```

#### Test 3: Stress Test

```bash
# Create 3 videos back-to-back
# Measure total time
# Expected: 3 × 210s = ~630 seconds (vs 990 before)
```

### Performance Checklist

| Metric | Before | Target | Actual | ✓ |
|--------|--------|--------|--------|---|
| Script generation | 60s | 60s | ___ | □ |
| Keyword generation | 30s | 25s | ___ | □ |
| 5 sentence keywords | 150s | 75s | ___ | □ |
| TTS generation | 60s | 20s | ___ | □ |
| **Total workflow** | **330s** | **210s** | ___ | □ |

### Success Criteria
- ✅ Total workflow time reduced by 30%+
- ✅ Both models work reliably
- ✅ No GPU OOM errors
- ✅ Video quality unchanged
- ✅ Keyword quality acceptable

---

## Phase 7: Documentation & Rollback Plan ⏱️ 1 hour

### Objective
Document changes and create rollback procedure.

### Documentation Tasks

1. **Update README**
   ```markdown
   ## GPU Optimization
   
   MoneyPrinterTurbo uses a dual model strategy for optimal performance:
   - **gemma4:e4b** (9.6GB) for script generation (quality)
   - **gemma:2b** (1.4GB) for keyword generation (speed)
   - **AllTalk GPU** for TTS acceleration
   
   This configuration provides ~36% faster video generation on 6GB GPUs.
   ```

2. **Create configuration guide**
   
   **File: `docs/DUAL_MODEL_SETUP.md`**
   ```markdown
   # Dual Model Configuration Guide
   
   ## Quick Start
   1. Pull models: `docker exec ollama ollama pull gemma:2b`
   2. Update config.toml with dual model settings
   3. Restart containers
   
   ## Configuration Options
   - `ollama_use_keyword_model`: Enable/disable dual model (default: true)
   - `ollama_model_name`: Primary model for scripts
   - `ollama_keyword_model`: Secondary model for keywords
   
   ## Troubleshooting
   - If keywords are poor quality: Set `ollama_use_keyword_model = false`
   - If OOM errors: Reduce keep_alive time
   ```

3. **Add to config.example.toml**
   ```toml
   # Dual Model Strategy (GPU Optimization)
   # Use different models for different tasks to optimize speed and VRAM usage
   ollama_model_name = "gemma4:e4b"         # Primary: script generation (quality)
   ollama_keyword_model = "gemma:2b"         # Secondary: keywords (speed)
   ollama_use_keyword_model = true           # Enable dual model feature
   ```

### Rollback Plan

**If dual model causes issues:**

1. **Quick rollback** (disable feature):
   ```toml
   # In config.toml
   ollama_use_keyword_model = false  # Back to single model
   ```

2. **Full rollback** (revert code):
   ```bash
   cd /mnt/data/repos/MoneyPrinterTurbo-openai-tts
   git stash  # Save current changes
   git checkout HEAD~1  # Revert to previous commit
   sudo docker compose restart moneyprinterturbo-dev-api
   ```

3. **Remove small model** (free disk space):
   ```bash
   docker exec ollama ollama rm gemma:2b
   ```

### Backup Current State

```bash
# Before starting implementation
cd /mnt/data/repos/MoneyPrinterTurbo-openai-tts
git add -A
git commit -m "Backup before dual model implementation"
git tag backup-before-dual-model
```

---

## Success Metrics

### Performance Goals
- ✅ **36% faster** overall workflow (330s → 210s)
- ✅ **50% faster** keyword generation (30s → 15s)
- ✅ **67% faster** TTS (60s → 20s)

### Quality Goals
- ✅ Script quality unchanged (using same model)
- ✅ Keyword quality acceptable (>90% as good)
- ✅ Audio quality maintained or improved

### Reliability Goals
- ✅ No GPU OOM errors during normal operation
- ✅ Model switching works reliably
- ✅ Fallback to single model if needed

---

## Timeline Summary

| Phase | Duration | Cumulative |
|-------|----------|------------|
| 1. Test small model | 30 min | 0.5h |
| 2. Add configuration | 30 min | 1.0h |
| 3. Implement routing | 2 hours | 3.0h |
| 4. Update endpoints | 30 min | 3.5h |
| 5. AllTalk GPU | 1 hour | 4.5h |
| 6. Testing | 2 hours | 6.5h |
| 7. Documentation | 1 hour | 7.5h |

**Total: ~7.5 hours**

---

## Go/No-Go Decision Points

### After Phase 1
**STOP if:** Keywords are poor quality  
**CONTINUE if:** Keywords are acceptable

### After Phase 3
**STOP if:** Model routing errors  
**CONTINUE if:** Both models work correctly

### After Phase 5
**STOP if:** GPU OOM errors persist  
**CONTINUE if:** GPU sharing works

### After Phase 6
**ROLLBACK if:** Performance worse or quality degraded  
**DEPLOY if:** Goals achieved

---

## Next Actions

1. ✅ **Review this plan**
2. ⏳ **Run Phase 1 test** (30 min)
3. ⏳ **Decide**: Proceed or stop based on quality
4. ⏳ **Execute phases 2-7** if approved

**Ready to start with Phase 1?**
