# Rollback Guide - Dual Model Optimization

## Quick Rollback (Recommended)

If you encounter issues with the dual model feature, you can disable it without removing any code:

### Step 1: Disable Feature in Config

Edit your config file (location depends on your setup):
- Development: `/mnt/samsungssd/docker/appdata/moneyprinterturbo-dev/config/config.toml`
- Or: `/mnt/data/repos/MoneyPrinterTurbo-openai-tts/config.toml`

Change:
```toml
# Disable dual model feature
ollama_use_keyword_model = false
```

### Step 2: Restart Container

```bash
docker restart moneyprinterturbo-dev-api
```

### Step 3: Verify

```bash
docker logs --tail 50 moneyprinterturbo-dev-api | grep "Using primary model"
```

You should see both script and keyword generation using the primary model.

---

## Complete Rollback (Git)

If you need to completely remove the dual model code:

### Step 1: Check Current Status

```bash
cd /mnt/data/repos/MoneyPrinterTurbo-openai-tts
git status
git log --oneline -5
```

### Step 2: Create Backup Tag

```bash
git tag dual-model-backup-$(date +%Y%m%d)
git push origin dual-model-backup-$(date +%Y%m%d)
```

### Step 3: Revert Changes

Option A - Stash changes (preserves work):
```bash
git stash save "dual-model-optimization"
```

Option B - Hard reset (removes changes):
```bash
# Find the commit before dual model changes
git log --oneline --all | grep -B5 "dual model"

# Reset to that commit (CAUTION: loses uncommitted changes)
git reset --hard <commit-hash>
```

### Step 4: Restart Services

```bash
docker restart moneyprinterturbo-dev-api
docker restart moneyprinterturbo-dev-webui  # if applicable
```

---

## Restore After Rollback

If you rolled back and want to restore the dual model feature:

### From Stash

```bash
git stash list  # Find your stash
git stash apply stash@{0}  # Replace {0} with your stash number
```

### From Tag/Backup

```bash
git checkout dual-model-backup-YYYYMMDD
# Or
git cherry-pick <commit-hash>
```

---

## Files Modified by Dual Model Feature

The following files were changed. You can manually revert them if needed:

**Configuration:**
- `config.toml` - Added dual model settings
- `config.example.toml` - Added documentation

**Code:**
- `app/services/llm.py` - Added `_get_ollama_model()`, modified `_generate_response()`
- `app/controllers/v1/llm.py` - No changes (already had `skip_unload`)
- `app/services/task.py` - No changes (already had `skip_unload`)

**Documentation:**
- `docs/DUAL_MODEL_SETUP.md` - New file
- `docs/IMPLEMENTATION_PLAN.md` - New file
- `docs/GPU_OPTIMIZATION_ANALYSIS.md` - New file
- `docs/test_small_model.sh` - New file
- `docs/ROLLBACK_DUAL_MODEL.md` - This file

---

## Manual Code Rollback

If you only want to revert specific code changes:

### Revert llm.py Changes

```bash
cd /mnt/data/repos/MoneyPrinterTurbo-openai-tts

# View changes
git diff app/services/llm.py

# Revert just this file
git checkout HEAD -- app/services/llm.py
```

### Revert Config Changes

```bash
# Backup current config
cp config.toml config.toml.backup

# Restore from example
cp config.example.toml config.toml

# Edit config.toml with your original settings
```

---

## Verification After Rollback

### Test Single Model Operation

```bash
# Generate keywords - should use primary model
curl -X POST http://localhost:8089/api/v1/terms \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: your-api-key" \
  -d '{"video_subject": "test", "video_script": "test script", "amount": 3}'

# Check logs - should see primary model for everything
docker logs --tail 100 moneyprinterturbo-dev-api | grep "ollama_model"
```

### Expected Behavior After Rollback

- Only `ollama_model_name` is used
- No "Using keyword model" messages in logs
- Keyword generation takes longer (uses large model)
- All functionality works as before

---

## Common Issues After Rollback

### Issue: Config not updating

**Solution:**
```bash
# Find the actual config location
docker inspect moneyprinterturbo-dev-api | grep -A5 "Mounts"

# Update the correct file
sudo nano /path/to/actual/config.toml

# Restart
docker restart moneyprinterturbo-dev-api
```

### Issue: Container won't start

**Solution:**
```bash
# Check for syntax errors in config
docker logs moneyprinterturbo-dev-api

# Verify TOML syntax
python3 -c "import toml; toml.load('config.toml')"
```

### Issue: Changes not taking effect

**Solution:**
```bash
# Hard restart with rebuild
docker stop moneyprinterturbo-dev-api
docker rm moneyprinterturbo-dev-api
# Then recreate container with docker-compose or your setup method
```

---

## Need Help?

If rollback fails or you encounter issues:

1. **Check logs:** `docker logs --tail 100 moneyprinterturbo-dev-api`
2. **Verify config:** Ensure `config.toml` syntax is correct
3. **Test basic functionality:** Try generating a simple video
4. **File an issue:** Include error logs and your rollback steps

---

## Safe Testing Before Rollback

Before doing a full rollback, you can test single-model operation:

```toml
# In config.toml, just disable the feature
ollama_use_keyword_model = false  # This line only

# Keep these lines (they won't hurt)
ollama_keyword_model = "gemma:2b"
```

This lets you quickly toggle between dual-model and single-model without code changes.
