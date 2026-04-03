# CODEMAP

This document provides a diagram-style codemap and a “read first” guide for the repository.

## System overview (UI/API → task pipeline → artifacts)

```mermaid
flowchart TD
  subgraph UI["UI Layer"]
    ST["Streamlit WebUI\nwebui/Main.py"]
  end

  subgraph API["API Layer (FastAPI)"]
    UV["Uvicorn entrypoint\nmain.py"]
    ASGI["ASGI app factory\napp/asgi.py"]
    ROUTER["Router registry\napp/router.py"]
    V1VIDEO["Video endpoints\napp/controllers/v1/video.py"]
    V1LLM["LLM endpoints\napp/controllers/v1/llm.py"]
  end

  subgraph CORE["Core Pipeline (Services)"]
    TASK["Task Orchestrator\napp/services/task.py::start()"]
    STATE["Task state store\napp/services/state.py"]
    LLM["LLM provider adapter\napp/services/llm.py"]
    VOICE["TTS + subtitle maker\napp/services/voice.py"]
    SUB["Subtitle generation/correction\napp/services/subtitle.py"]
    MAT["Material download\napp/services/material.py"]
    VID["Video compose/render\napp/services/video.py"]
  end

  subgraph CFG["Configuration"]
    TOML["config.toml / config.example.toml"]
    CONF["Config loader\napp/config/config.py"]
  end

  subgraph STORAGE["Storage / Artifacts"]
    TASKDIR["Per-task directory\nstorage/tasks/<task_id>/\n(audio.mp3, subtitle.srt, combined-*.mp4, final-*.mp4, script.json)"]
    RES["Resources\nresource/fonts, resource/songs"]
    LOCALVID["Local uploads\nstorage/local_videos/"]
  end

  UV --> ASGI --> ROUTER
  ROUTER --> V1VIDEO
  ROUTER --> V1LLM

  ST --> CONF
  V1VIDEO --> TASK
  V1LLM --> LLM

  TOML --> CONF
  CONF --> TASK
  CONF --> LLM
  CONF --> VOICE
  CONF --> MAT
  CONF --> VID

  TASK --> STATE
  TASK --> LLM
  TASK --> VOICE
  TASK --> SUB
  TASK --> MAT
  TASK --> VID

  MAT --> TASKDIR
  VOICE --> TASKDIR
  SUB --> TASKDIR
  VID --> TASKDIR

  RES --> VID
  LOCALVID --> MAT
```

## Detailed pipeline (what `task.start()` does)

```mermaid
sequenceDiagram
  participant Client as WebUI/API Client
  participant Controller as FastAPI Controller (v1/video.py)
  participant Task as Task Orchestrator (services/task.py)
  participant LLM as LLM (services/llm.py)
  participant Voice as TTS (services/voice.py)
  participant Sub as Subtitles (services/subtitle.py)
  participant Mat as Materials (services/material.py)
  participant Vid as Video (services/video.py)
  participant State as State (services/state.py)
  participant FS as Filesystem (storage/tasks/<task_id>/)

  Client->>Controller: POST /videos (VideoParams)
  Controller->>State: init task record
  Controller->>Task: enqueue start(task_id, params, stop_at="video")

  Task->>State: state=processing, progress updates
  Task->>LLM: generate_script (if video_script empty)
  Task->>LLM: generate_terms (if not local source)
  Task->>FS: write script.json

  Task->>Voice: tts(text) OR use custom audio file
  Voice->>FS: write audio.mp3

  alt subtitles enabled and TTS sub_maker available
    Task->>Voice: create_subtitle(edge)
    Voice->>FS: write subtitle.srt
  else fallback
    Task->>Sub: whisper create + correct
    Sub->>FS: write subtitle.srt
  end

  Task->>Mat: download_videos(...) OR local preprocess
  Mat->>FS: write downloaded clips into task dir (or reference local files)

  loop video_count times
    Task->>Vid: combine_videos(...)
    Vid->>FS: write combined-i.mp4
    Task->>Vid: generate_video(...) (overlay subs + mix bgm)
    Vid->>FS: write final-i.mp4
  end

  Task->>State: state=complete + results (paths)
  Client->>Controller: GET /tasks/{task_id}
  Controller-->>Client: URLs rewritten to /tasks/... for download/stream
```

## Most important files to read first (in order)

- **README.md / README-en.md**
  - How to run WebUI + API, required dependencies, expected behavior.
- **main.py**
  - API server entrypoint (Uvicorn) → `app.asgi:app`.
- **app/asgi.py**
  - FastAPI app creation, middleware, static mounts.
- **app/router.py**
  - Router registry (what endpoints are exposed).
- **app/controllers/v1/video.py**
  - Task creation, query/delete, uploads, streaming/downloading.
- **app/services/task.py**
  - Authoritative end-to-end pipeline orchestration (`start()`).
- **app/models/schema.py**
  - `VideoParams` (core config object) and enums.
- **app/services/video.py**
  - Video composition/rendering.
- **app/services/voice.py**
  - TTS provider integrations + subtitle creation helpers.
- **app/services/material.py**
  - Stock video search/download logic.
- **app/config/config.py + config.example.toml**
  - Config keys and defaults.
- **webui/Main.py**
  - Streamlit UI wiring.
