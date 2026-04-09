# Ollama Automatic Model Detection

## Overview

The WebUI now automatically fetches available Ollama models from your Ollama server, eliminating the need to manually type model names from `ollama list`.

## Features

✅ **Automatic Model Discovery** - Fetches models directly from Ollama API  
✅ **Dropdown Selection** - Choose from available models instead of typing  
✅ **Real-time Refresh** - Update model list with a button click  
✅ **Fallback Support** - Manual entry still available if auto-fetch fails  
✅ **Smart URL Handling** - Automatically handles both `/v1` and non-`/v1` endpoints  
✅ **Error Handling** - Clear messages if Ollama is unreachable  

## How It Works

### 1. **Configure Ollama Base URL**

In the WebUI sidebar, select **Ollama** as your LLM provider and enter your Ollama server URL:

```
http://localhost:11434/v1
```

Or for Docker/remote setups:
```
http://192.168.0.116:11436/v1
http://host.docker.internal:11436/v1
```

### 2. **Automatic Model Fetch**

When you enter the Base URL, the system automatically:
- Calls the Ollama API at `/api/tags`
- Retrieves all available models
- Caches the list for performance
- Displays models in a dropdown

### 3. **Select Your Model**

Choose from the dropdown list of available models:
- `llama2:7b`
- `qwen:7b`
- `codellama:13b`
- etc.

### 4. **Refresh Models**

If you pull new models after the WebUI has started, click the **🔄 Refresh** button to update the list.

### 5. **Manual Entry (Optional)**

If auto-detection fails or you want to use a custom model:
1. Check the **"Use custom model name"** checkbox
2. Enter the model name manually

## Configuration

### Environment Variables

Add to your `.env` file:
```bash
# Ollama service URL
OLLAMA_BASE_URL=http://192.168.0.116:11436/v1
```

### In config.toml

```toml
[app]
llm_provider = "ollama"
ollama_base_url = "http://192.168.0.116:11436/v1"
ollama_model_name = "qwen:7b"  # Will be auto-populated from dropdown
```

## API Endpoints Used

The helper uses the standard Ollama API:

### List Models
```
GET http://localhost:11434/api/tags
```

Response:
```json
{
  "models": [
    {
      "name": "llama2:7b",
      "modified_at": "2024-01-15T12:00:00Z",
      "size": 3826793677
    },
    {
      "name": "qwen:7b",
      "modified_at": "2024-01-15T13:00:00Z",
      "size": 4108916909
    }
  ]
}
```

## Implementation Details

### Files Created/Modified

#### New File: `webui/utils/ollama_helper.py`
Contains helper functions:
- `fetch_ollama_models()` - Get model list from API
- `test_ollama_connection()` - Verify server connectivity
- `get_model_display_name()` - Format model names for UI
- `get_ollama_model_info()` - Get detailed model information

#### Modified: `webui/components/llm_config.py`
- Added import of ollama_helper
- Special handling for Ollama provider
- Dropdown selection with model list
- Refresh button functionality
- Fallback to manual entry

### Caching

Model lists are cached in Streamlit session state (`ollama_models_cache`) to avoid repeated API calls. Cache is refreshed when:
- User clicks the Refresh button
- Page is reloaded
- Session state is cleared

## Troubleshooting

### Cannot Connect to Ollama

**Error Message:**
```
⚠️ Cannot connect to Ollama at http://localhost:11434
```

**Solutions:**
1. Verify Ollama is running: `docker ps | grep ollama`
2. Check the URL is correct (port 11436 for your setup, not 11434)
3. For Docker: Use `host.docker.internal` instead of `localhost`
4. Check firewall/network settings

### No Models Found

**Error Message:**
```
No models found on Ollama server
```

**Solutions:**
1. Pull at least one model: `docker exec ollama ollama pull qwen:7b`
2. List models to verify: `docker exec ollama ollama list`
3. Refresh the model list in WebUI

### Request Timeout

**Error Message:**
```
⚠️ Ollama API request timed out after 5s
```

**Solutions:**
1. Check network latency to Ollama server
2. Increase timeout in code if needed (default: 5s)
3. Verify Ollama server is responsive: `curl http://192.168.0.116:11436/api/tags`

### Models Not Updating

**Solutions:**
1. Click the **🔄 Refresh** button
2. Reload the WebUI page
3. Clear browser cache
4. Check Ollama logs: `docker logs ollama`

## Example Setup

### Your Configuration

Based on your setup with Ollama on `192.168.0.116:11436`:

**In WebUI:**
1. Select **Ollama** as LLM provider
2. Enter Base URL: `http://192.168.0.116:11436/v1`
3. Wait for models to load automatically
4. Select model from dropdown (e.g., `qwen:7b`)
5. Enter API Key: `123` (any value works)
6. Click **Save Configuration**

**The system will:**
- Strip the `/v1` suffix → `http://192.168.0.116:11436`
- Call `http://192.168.0.116:11436/api/tags`
- Parse model list
- Display in dropdown

## Advanced Usage

### Get Model Information

The `get_ollama_model_info()` function can retrieve detailed model info:

```python
from webui.utils.ollama_helper import get_ollama_model_info

info = get_ollama_model_info(
    base_url="http://192.168.0.116:11436/v1",
    model_name="qwen:7b"
)
# Returns: model details including size, parameters, etc.
```

### Test Connection Before Using

```python
from webui.utils.ollama_helper import test_ollama_connection

success, error = test_ollama_connection("http://192.168.0.116:11436/v1")
if success:
    print("✅ Connected to Ollama")
else:
    print(f"❌ Error: {error}")
```

## Benefits

**Before (Manual):**
1. SSH into Ollama server or container
2. Run `ollama list`
3. Copy model name
4. Paste into WebUI
5. Hope you didn't make a typo

**After (Automatic):**
1. Select Ollama provider
2. Enter server URL
3. Pick model from dropdown
4. Done! ✨

## Future Enhancements

Potential improvements:
- [ ] Show model size and modification date
- [ ] Filter models by type (text, code, etc.)
- [ ] Auto-detect Ollama URL from common locations
- [ ] Model performance indicators
- [ ] Pull new models directly from WebUI
- [ ] Show model parameters and capabilities

## Related Documentation

- [LOGGING_SETUP.md](LOGGING_SETUP.md) - Logging configuration
- [INTEGRATION_COMPLETE.md](INTEGRATION_COMPLETE.md) - Integration guide
- [Ollama API Documentation](https://github.com/ollama/ollama/blob/main/docs/api.md)
