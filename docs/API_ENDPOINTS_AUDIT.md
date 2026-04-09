# API Endpoints Audit & Reference

**Date:** April 9, 2026  
**Status:** ✅ All endpoints verified and corrected

---

## 📋 Backend API Routes (FastAPI)

### **LLM Endpoints** (`app/controllers/v1/llm.py`)

| Method | Endpoint | Purpose | WebUI Usage |
|--------|----------|---------|-------------|
| `POST` | `/api/v1/scripts` | Generate video script from subject | ✅ `Main.py:284` |
| `POST` | `/api/v1/terms` | Generate search keywords from script | ✅ `Main.py:305, 331` |

### **Video/Task Endpoints** (`app/controllers/v1/video.py`)

| Method | Endpoint | Purpose | WebUI Usage |
|--------|----------|---------|-------------|
| `POST` | `/api/v1/videos` | Create video generation task | ✅ `task_creation.py:43, 117` |
| `POST` | `/api/v1/subtitle` | Generate subtitle only | ❌ Not used in WebUI |
| `POST` | `/api/v1/audio` | Generate audio only | ❌ Not used in WebUI |
| `GET` | `/api/v1/tasks` | Get all tasks (paginated) | ⚠️ Used in backup file only |
| `GET` | `/api/v1/tasks/{task_id}` | Query task status | ⚠️ Used in backup file only |
| `DELETE` | `/api/v1/tasks/{task_id}` | Delete task | ❌ Not used in WebUI |
| `GET` | `/api/v1/musics` | Retrieve local BGM files | ❌ Not used in WebUI |
| `POST` | `/api/v1/musics` | Upload BGM file | ❌ Not used in WebUI |
| `GET` | `/api/v1/video_materials` | Retrieve local video materials | ❌ Not used in WebUI |
| `POST` | `/api/v1/video_materials` | Upload video material | ❌ Not used in WebUI |
| `POST` | `/api/v1/stock_videos/search` | Search Pexels/Pixabay videos | ⚠️ Used in backup file only |
| `GET` | `/api/v1/stream/{file_path}` | Stream video file | ❌ Not used in WebUI |
| `GET` | `/api/v1/download/{file_path}` | Download video file | ❌ Not used in WebUI |

---

## 🔧 Fixed Endpoints

### **Issue 1: Wrong Video Creation Endpoint**

**Before:**
```python
# ❌ WRONG - This endpoint doesn't exist
create_url = f"{api_base_url}/api/v1/video/create"
```

**After:**
```python
# ✅ CORRECT - Matches FastAPI route
create_url = f"{api_base_url}/api/v1/videos"
```

**Files Fixed:**
- `webui/components/task_creation.py:43` ✅
- `webui/components/task_creation.py:117` ✅

### **Issue 2: Wrong Script/Terms Endpoints (Previously Fixed)**

**Before:**
```python
# ❌ WRONG - Extra /llm/ in path
f"{api_base_url}/api/v1/llm/scripts"
f"{api_base_url}/api/v1/llm/terms"
```

**After:**
```python
# ✅ CORRECT - Router already prefixes with /api/v1
f"{api_base_url}/api/v1/scripts"
f"{api_base_url}/api/v1/terms"
```

**Files Fixed:**
- `webui/Main.py:284` ✅
- `webui/Main.py:305` ✅
- `webui/Main.py:331` ✅

---

## 📊 Current WebUI API Usage

### **Active Endpoints in Main.py**

```python
# Script Generation
POST /api/v1/scripts
{
    "video_subject": "home improvement",
    "video_language": "en",
    "paragraph_number": 1
}

# Global Keywords Generation
POST /api/v1/terms
{
    "video_subject": "home improvement",
    "video_script": "generated script...",
    "amount": 10
}

# Sentence-Level Keywords Generation (per sentence)
POST /api/v1/terms
{
    "video_subject": "Every homeowner can transform...",
    "video_script": "Every homeowner can transform their space...",
    "amount": 5
}
```

### **Active Endpoints in task_creation.py**

```python
# Create Video Task
POST /api/v1/videos
{
    "video_subject": "topic",
    "video_script": "script...",
    "video_terms": "keywords...",
    "video_aspect": "16:9",
    "video_concat_mode": "sequential",
    "video_clip_duration": 5,
    "video_count": 1,
    "video_language": "en",
    "video_source": "pexels",
    "voice_name": "nova",
    "voice_rate": 1.0,
    "voice_volume": 1.0,
    "voice_pitch": 1.0,
    "bgm_type": "random",
    "bgm_volume": 0.2,
    "subtitle_enabled": true,
    "n_threads": 2,
    "paragraph_number": 1
}

# Bulk Create (loops through topics)
POST /api/v1/videos  (called multiple times)
```

---

## ⚠️ Deprecated/Backup File Endpoints

These endpoints exist in `Main_original_backup_20260408_220918.py` but are NOT used in the current WebUI:

```python
# Stock Video Search (backup file only)
POST /api/v1/stock_videos/search

# Task Query (backup file only)
GET /api/v1/tasks/{task_id}

# Video Creation (backup file - same as current)
POST /api/v1/videos
```

---

## 🚀 Endpoint Usage Summary

### **Currently Used (Active)**
- ✅ `POST /api/v1/scripts` - Script generation
- ✅ `POST /api/v1/terms` - Keyword generation (global + per-sentence)
- ✅ `POST /api/v1/videos` - Video task creation

### **Available But Not Used**
- ❌ `POST /api/v1/subtitle` - Subtitle-only generation
- ❌ `POST /api/v1/audio` - Audio-only generation
- ❌ `GET /api/v1/tasks` - List all tasks
- ❌ `GET /api/v1/tasks/{task_id}` - Query task status
- ❌ `DELETE /api/v1/tasks/{task_id}` - Delete task
- ❌ `GET /api/v1/musics` - List BGM files
- ❌ `POST /api/v1/musics` - Upload BGM
- ❌ `GET /api/v1/video_materials` - List video materials
- ❌ `POST /api/v1/video_materials` - Upload video material
- ❌ `POST /api/v1/stock_videos/search` - Search stock videos
- ❌ `GET /api/v1/stream/{file_path}` - Stream video
- ❌ `GET /api/v1/download/{file_path}` - Download video

---

## 🔍 Verification Commands

### **Check Backend Routes**
```bash
# View all registered FastAPI routes
docker exec moneyprinterturbo-dev-api python -c "
from app.router import root_api_router
for route in root_api_router.routes:
    print(f'{route.methods} {route.path}')
"
```

### **Test Endpoints**
```bash
# Test script generation
curl -X POST http://192.168.0.116:8089/api/v1/scripts \
  -H "Content-Type: application/json" \
  -d '{"video_subject": "test", "video_language": "en", "paragraph_number": 1}'

# Test keyword generation
curl -X POST http://192.168.0.116:8089/api/v1/terms \
  -H "Content-Type: application/json" \
  -d '{"video_subject": "test", "video_script": "test script", "amount": 5}'

# Test video creation
curl -X POST http://192.168.0.116:8089/api/v1/videos \
  -H "Content-Type: application/json" \
  -d '{"video_subject": "test", "video_script": "test", "video_terms": "test"}'
```

---

## 📝 Notes

1. **Router Prefixing:** All v1 routes use `new_router()` which automatically adds `/api/v1` prefix
2. **No `/llm/` in paths:** The llm router is included directly, not nested under `/llm/`
3. **Plural vs Singular:** Use `/videos` (plural), not `/video/create`
4. **Task ID Format:** Task IDs are UUIDs returned in response `data.task_id`

---

## ✅ Verification Status

| Component | Status | Notes |
|-----------|--------|-------|
| Script Generation | ✅ Fixed | Changed from `/llm/scripts` to `/scripts` |
| Keyword Generation | ✅ Fixed | Changed from `/llm/terms` to `/terms` |
| Video Creation | ✅ Fixed | Changed from `/video/create` to `/videos` |
| Bulk Creation | ✅ Fixed | Uses corrected `/videos` endpoint |

**All endpoints now match the backend FastAPI routes!** 🎉
