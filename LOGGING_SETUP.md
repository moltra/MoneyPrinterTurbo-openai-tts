# Logging Setup Documentation

## Overview

MoneyPrinterTurbo WebUI now includes centralized logging configuration with support for:
- ✅ Console logging with colors and detailed formatting
- ✅ File logging with automatic rotation and compression
- ✅ Task-specific logging for video generation jobs
- ✅ Configurable log levels and retention
- ✅ Thread-safe logging operations

## Files Added

### 1. `webui/logging_config.py`
Centralized logging configuration module with functions:
- `setup_webui_logging()` - Main logging setup
- `get_task_logger(task_id)` - Task-specific logger
- `log_system_info()` - Log startup information
- `disable_logging()` / `enable_logging()` - For testing

### 2. `.env.example`
Environment variable template with:
- Deployment configuration (dev/prod)
- API URLs (internal and public)
- Docker settings (timezone, user IDs)
- CORS configuration
- Optional service URLs (Redis, Ollama, AllTalk)

## Configuration

### Log Levels
Set via environment variable or config.toml:
```bash
# In .env
LOG_LEVEL=INFO  # Options: DEBUG, INFO, WARNING, ERROR
```

Or in `config.toml`:
```toml
log_level = "INFO"
```

### File Logging
Enable file logging in `config.toml`:
```toml
[app]
# Enable file logging
log_file_enabled = true
log_file_path = "./storage/logs/webui.log"
log_rotation = "500 MB"  # Rotate when file reaches 500MB
log_retention = "30 days"  # Keep logs for 30 days
```

### Log Output Locations

#### Console Logs
- Colored output to stdout
- Format: `YYYY-MM-DD HH:mm:ss | LEVEL | module:function:line - message`
- Always enabled

#### File Logs (if enabled)
- Main log: `./storage/logs/webui.log`
- Task logs: `./storage/logs/tasks/{task_id}.log`
- Rotated logs: Automatically compressed to `.zip`
- Old logs: Automatically deleted after retention period

## Integration

### WebUI Main.py
The logging is automatically initialized when the application starts:

```python
# In webui/Main.py (lines 32-35)
from webui.logging_config import setup_webui_logging, log_system_info
setup_webui_logging()
log_system_info()
```

### Task-Specific Logging
For video generation tasks, use task-specific loggers:

```python
from webui.logging_config import get_task_logger

# Create task logger
task_logger = get_task_logger(task_id="task-123")

# Use it
task_logger.info("Starting video generation")
task_logger.debug(f"Parameters: {params}")
task_logger.error("Failed to download video clip")
```

## Log Format

### Console Output (Colored)
```
2026-04-09 10:43:15 | INFO     | webui.Main:main:387 - Starting MoneyPrinterTurbo WebUI
2026-04-09 10:43:15 | INFO     | app.config:__init__:78 - MoneyPrinterTurbo (Self-Hosted) v1.2.7-selfhosted.1
2026-04-09 10:43:16 | DEBUG    | webui.components.llm_config:render_llm_config:186 - Rendering LLM configuration
```

### File Output (Plain Text)
```
2026-04-09 10:43:15 | INFO     | webui.Main:main:387 - Starting MoneyPrinterTurbo WebUI
2026-04-09 10:43:15 | INFO     | app.config:__init__:78 - MoneyPrinterTurbo (Self-Hosted) v1.2.7-selfhosted.1
2026-04-09 10:43:16 | DEBUG    | webui.components.llm_config:render_llm_config:186 - Rendering LLM configuration
```

### Task Log Format
```
2026-04-09 10:45:00 | INFO     | task-abc123 | Starting video generation
2026-04-09 10:45:05 | DEBUG    | task-abc123 | Downloaded clip 1/5
2026-04-09 10:45:10 | ERROR    | task-abc123 | Failed to merge videos: ffmpeg error
```

## Startup Information

When the WebUI starts, it logs system information:
```
============================================================
MoneyPrinterTurbo WebUI Starting
============================================================
Project: MoneyPrinterTurbo (Self-Hosted)
Version: 1.2.7-selfhosted.1
Python: 3.10.12
Platform: Linux 5.15.0-91-generic
Hostname: your-hostname
Log Level: INFO
Mode: DEV
============================================================
```

## Log Rotation

Logs are automatically rotated based on size:
- Default: 500 MB per file
- Rotated files: `webui.log.2026-04-09_10-43-15.zip`
- Compression: Automatic ZIP compression
- Cleanup: Old logs deleted after retention period (default: 30 days)

## Environment Variables

### Docker Compose
The updated `moneyprinterturbo-dev-clean.yml` now includes:
```yaml
env_file:
  - .env  # Load environment variables from .env file

environment:
  - TZ=${TZ}
  - PYTHONUNBUFFERED=1  # Ensures logs appear in real-time
  - MPT_MODE=dev
  - MPT_API_BASE_URL=${MPT_API_BASE_URL:-http://moneyprinterturbo-dev-api:8080}
  - STREAMLIT_SERVER_HEADLESS=true
  - STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
  - STREAMLIT_SERVER_ENABLE_CORS=true
```

### .env File Setup

1. Copy the template:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your values:
   ```bash
   # Deployment mode
   MPT_MODE=dev

   # API URLs
   MPT_API_BASE_URL=http://moneyprinterturbo-dev-api:8080
   MPT_PUBLIC_API_BASE_URL=http://192.168.0.116:8089

   # Docker paths
   DOCKERDIR=/home/user/docker
   MPT_REPO_DIR=/mnt/data/repos/MoneyPrinterTurbo-openai-tts

   # Timezone
   TZ=America/New_York

   # User IDs
   PUID=1000
   PGID=1000
   ```

3. The `.env` file is already in `.gitignore` to protect sensitive data

## .gitignore Updates

The `.gitignore` file has been enhanced to exclude:
- ✅ `.env` and all `.env.*` files
- ✅ Log files (`*.log`, `logs/`, `/storage/logs/`)
- ✅ Virtual environments
- ✅ IDE files
- ✅ Temporary files and caches

## Testing

### Check Console Logging
```bash
# Start the WebUI and check console output
docker compose -f moneyprinterturbo-dev-clean.yml up moneyprinterturbo-dev-webui
```

### Check File Logging
```bash
# Enable file logging in config.toml first, then:
docker exec moneyprinterturbo-dev-webui ls -lh /MoneyPrinterTurbo/storage/logs/
docker exec moneyprinterturbo-dev-webui tail -f /MoneyPrinterTurbo/storage/logs/webui.log
```

### Check Task Logging
After generating a video, check task-specific logs:
```bash
docker exec moneyprinterturbo-dev-webui ls -lh /MoneyPrinterTurbo/storage/logs/tasks/
docker exec moneyprinterturbo-dev-webui cat /MoneyPrinterTurbo/storage/logs/tasks/{task_id}.log
```

## Troubleshooting

### Logs Not Appearing in Console
- Check `PYTHONUNBUFFERED=1` is set in docker-compose
- Verify log level is not set too high (e.g., ERROR when you want INFO)

### File Logs Not Created
- Ensure `log_file_enabled = true` in `config.toml`
- Check write permissions on `./storage/logs/` directory
- Verify the container user has write access (PUID/PGID settings)

### Log Files Growing Too Large
- Reduce `log_rotation` value (e.g., "100 MB")
- Reduce `log_retention` period (e.g., "7 days")
- Set log level to WARNING or ERROR instead of DEBUG

### Permission Errors
If you see permission errors when writing logs:
```bash
# On the host, fix permissions:
sudo chown -R 1000:1000 /mnt/data/storage/logs
sudo chmod -R 755 /mnt/data/storage/logs
```

## Best Practices

1. **Development**: Use `DEBUG` or `INFO` level
2. **Production**: Use `WARNING` or `ERROR` level
3. **File logging**: Enable in production for troubleshooting
4. **Log retention**: Keep 7-30 days based on disk space
5. **Sensitive data**: Never log API keys or passwords
6. **Task logs**: Enable for debugging video generation issues

## Next Steps

To further enhance logging:
1. Add logging to video generation components
2. Implement log viewer in WebUI
3. Add metrics collection (processing time, error rates)
4. Set up log aggregation (if using multiple containers)
5. Add alerting for critical errors

## Related Files

- `webui/logging_config.py` - Logging configuration
- `webui/Main.py` - WebUI entry point with logging initialization
- `.env.example` - Environment variable template
- `.gitignore` - Git ignore patterns (includes logs)
- `config.example.toml` - Configuration template
- `moneyprinterturbo-dev-clean.yml` - Docker Compose configuration
