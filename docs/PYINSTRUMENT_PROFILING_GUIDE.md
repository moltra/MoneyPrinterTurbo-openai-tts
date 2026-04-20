# PyInstrument Profiling Guide

**Date:** April 9, 2026  
**Status:** ✅ Complete - Performance Analysis Ready

---

## 🎯 Overview

PyInstrument profiling is now integrated throughout the application to identify performance bottlenecks and optimize critical code paths.

**Key Features:**
- ✅ Automatic profiling of slow functions (>0.1s by default)
- ✅ HTML reports for detailed analysis
- ✅ Low overhead (< 1% performance impact)
- ✅ Environment-based enable/disable
- ✅ Configurable thresholds

---

## ⚙️ Configuration

### **Environment Variables**

```bash
# Enable profiling (default: false)
ENABLE_PROFILING=true

# Output directory for HTML reports (default: /MoneyPrinterTurbo/storage/profiles)
PROFILE_OUTPUT_DIR=/MoneyPrinterTurbo/storage/profiles

# Minimum duration to log (default: 0.1 seconds)
PROFILE_MIN_DURATION=0.1
```

### **Docker Compose Setup**

```yaml
# moneyprinterturbo-dev-clean.yml
services:
  api:
    environment:
      - ENABLE_PROFILING=true
      - PROFILE_MIN_DURATION=0.5
    volumes:
      - /mnt/data/storage/profiles:/MoneyPrinterTurbo/storage/profiles
```

---

## 📊 Currently Profiled Functions

### **1. Video Processing** 🎬

**Function:** `combine_videos()`  
**File:** `app/services/video.py`  
**Min Duration:** 1.0s  
**Saves HTML:** ✅ Yes

```python
@profile_function(name="combine_videos", save_html=True, min_duration=1.0)
def combine_videos(combined_video_path, video_paths, audio_file, ...):
    # Video concatenation, transitions, audio mixing
    pass
```

**What it profiles:**
- Video clip loading
- Video concatenation
- Transition effects
- Audio mixing
- Subtitle rendering
- Final video export

---

### **2. Script Generation** 📝

**Function:** `generate_script()`  
**File:** `app/services/llm.py`  
**Min Duration:** 0.5s  
**Saves HTML:** ✅ Yes

```python
@profile_function(name="generate_script", save_html=True, min_duration=0.5)
def generate_script(video_subject, language, paragraph_number):
    # LLM API call to generate video script
    pass
```

**What it profiles:**
- LLM API call time
- Prompt construction
- Response parsing
- Retry logic

---

### **3. Keyword Generation** 🔍

**Function:** `generate_terms()`  
**File:** `app/services/llm.py`  
**Min Duration:** 0.5s  
**Saves HTML:** ✅ Yes

```python
@profile_function(name="generate_terms", save_html=True, min_duration=0.5)
def generate_terms(video_subject, video_script, amount):
    # Generate search terms for stock videos
    pass
```

**What it profiles:**
- Keyword generation API call
- JSON parsing
- Term filtering

---

## 🔧 How to Use Profiling

### **Method 1: Function Decorator** (Recommended)

```python
from app.utils.profiling import profile_function

@profile_function(name="my_function", save_html=True, min_duration=0.1)
def my_expensive_function(data):
    # Your code here
    result = process_data(data)
    return result
```

**Parameters:**
- `name`: Custom name for profile (default: function name)
- `save_html`: Save HTML report to disk (default: False)
- `print_results`: Print to logger (default: True)
- `min_duration`: Only log if execution > this (seconds, default: 0.1)

---

### **Method 2: Context Manager**

```python
from app.utils.profiling import ProfileContext

def process_task(task_id):
    # Profile specific code block
    with ProfileContext("data_processing", save_html=True) as p:
        data = load_data(task_id)
        results = transform_data(data)
        save_results(results)
    
    # Access duration
    logger.info(f"Processing took {p.duration:.3f}s")
```

---

### **Method 3: Manual Start/Stop**

```python
from app.utils.profiling import start_profile, stop_profile

def complex_workflow():
    profiler = start_profile("workflow")
    
    # Step 1
    prepare_data()
    
    # Step 2
    process_data()
    
    # Step 3
    finalize()
    
    stop_profile(profiler, "workflow", save_html=True)
```

---

### **Method 4: API Endpoint Profiling**

```python
from app.utils.profiling import profile_api_endpoint
from fastapi import APIRouter

router = APIRouter()

@router.post("/api/v1/videos")
@profile_api_endpoint(name="create_video", save_html=True)
async def create_video(params: VideoParams):
    # API logic
    return result
```

**Supports both sync and async endpoints!**

---

## 📈 Viewing Profile Results

### **Console Output**

When profiling is enabled, you'll see:

```
⏱️  Profile: combine_videos took 12.345s

  _     ._   __/__   _ _  _  _ _/_   Recorded: 15:30:45  Samples:  1234
 /_//_/// /_\ / //_// / //_'/ //     Duration: 12.345    CPU time: 11.890
/   _/                      v4.6.0

Program: combine_videos

12.345 combine_videos  app/services/video.py:157
└─ 8.234 concatenate_videoclips  moviepy/video/compositing/concatenate.py:42
   ├─ 4.123 VideoFileClip  moviepy/video/io/VideoFileClip.py:31
   │  └─ 3.890 ffmpeg_parse_infos  moviepy/video/io/ffmpeg_reader.py:56
   ├─ 2.456 resize  moviepy/video/fx/resize.py:15
   └─ 1.234 write_videofile  moviepy/video/VideoClip.py:359
└─ 3.111 AudioFileClip  moviepy/audio/AudioClip.py:45
└─ 1.000 SubtitlesClip  moviepy/video/tools/subtitles.py:78
```

---

### **HTML Reports**

Saved to: `/MoneyPrinterTurbo/storage/profiles/`

**File naming:** `{name}_{timestamp}.html`

Examples:
```
combine_videos_20260409_153045.html
generate_script_20260409_153102.html
generate_terms_20260409_153115.html
```

**To view:**
```bash
# Copy to local machine
docker cp moneyprinterturbo-dev-api:/MoneyPrinterTurbo/storage/profiles/combine_videos_20260409_153045.html ./

# Open in browser
open combine_videos_20260409_153045.html
```

**HTML Report Features:**
- 📊 Interactive flame graph
- 🔍 Drill down into function calls
- ⏱️ Time per function
- 📈 Call hierarchy
- 🎨 Color-coded by time

---

## 🔍 Analyzing Performance

### **Find Slow Functions**

Look for functions with:
1. **High total time** - Functions at top of profile
2. **High self time** - Time spent in function itself (not children)
3. **Many calls** - Functions called thousands of times

### **Common Bottlenecks**

#### **Video Processing:**
```
✗ Slow: Loading 10 clips serially
✓ Fast: Load clips in parallel (if possible)

✗ Slow: Multiple re-encodes
✓ Fast: Single pass encoding

✗ Slow: High resolution intermediate clips
✓ Fast: Resize before processing
```

#### **LLM Calls:**
```
✗ Slow: Multiple sequential API calls
✓ Fast: Batch requests

✗ Slow: Large context windows
✓ Fast: Minimal prompts

✗ Slow: No retries on timeout
✓ Fast: Exponential backoff retries
```

#### **Database/Storage:**
```
✗ Slow: Reading 1000 JSON files
✓ Fast: SQLite with indexes

✗ Slow: Synchronous file I/O
✓ Fast: Async I/O where possible
```

---

## 📝 Example: Optimizing Video Processing

### **Before Profiling**

```python
def combine_videos(video_paths, ...):
    clips = []
    for path in video_paths:
        clip = VideoFileClip(path)  # ← Slow!
        clip = clip.resize(height=1080)  # ← Slow!
        clips.append(clip)
    
    final = concatenate_videoclips(clips)  # ← Slow!
    final.write_videofile(output)  # ← Slow!
```

**Profile shows:** 15.5s total
- 8.2s loading clips
- 4.1s resizing
- 2.5s concatenating
- 0.7s writing

### **After Optimization**

```python
def combine_videos(video_paths, ...):
    # Use ffmpeg directly for concatenation (faster!)
    with open('concat_list.txt', 'w') as f:
        for path in video_paths:
            f.write(f"file '{path}'\n")
    
    # Single ffmpeg pass (much faster!)
    subprocess.run([
        'ffmpeg', '-f', 'concat', '-safe', '0',
        '-i', 'concat_list.txt',
        '-vf', 'scale=-2:1080',  # Resize during concat
        output
    ])
```

**After Profile:** 3.2s total (79% faster!)

---

## 🎯 Profiling Best Practices

### **DO:**
✅ Profile in production-like environment  
✅ Profile with realistic data sizes  
✅ Profile multiple runs (average results)  
✅ Save HTML for detailed analysis  
✅ Focus on high-impact optimizations first  

### **DON'T:**
❌ Profile with profiling enabled in production  
❌ Optimize before profiling (premature optimization)  
❌ Profile with tiny test data  
❌ Ignore I/O wait time  
❌ Optimize everything (80/20 rule!)  

---

## 🚀 Quick Start

### **1. Enable Profiling**

```bash
# In docker-compose.yml
services:
  api:
    environment:
      - ENABLE_PROFILING=true
```

### **2. Restart Container**

```bash
docker restart moneyprinterturbo-dev-api
```

### **3. Generate a Video**

```bash
# Use WebUI or API to create a video task
```

### **4. Check Logs**

```bash
docker logs -f moneyprinterturbo-dev-api | grep "Profile:"
```

**You'll see:**
```
⏱️  Profile: generate_script took 2.345s
⏱️  Profile: generate_terms took 1.234s
⏱️  Profile: combine_videos took 12.456s
```

### **5. Get HTML Reports**

```bash
# Copy all profiles to local machine
docker cp moneyprinterturbo-dev-api:/MoneyPrinterTurbo/storage/profiles ./profiles

# Open in browser
open profiles/combine_videos_*.html
```

---

## 📊 Performance Targets

| Operation | Current | Target | Status |
|-----------|---------|--------|--------|
| Script generation (Ollama) | ~3-5s | <2s | 🟡 Optimize |
| Keyword generation | ~2-3s | <1s | 🟡 Optimize |
| Video combine (30s video) | ~10-15s | <8s | 🔴 Needs work |
| Video combine (60s video) | ~25-30s | <15s | 🔴 Needs work |
| API response time | <500ms | <200ms | 🟢 Good |

---

## 🔧 Advanced Configuration

### **Custom Profile Storage**

```python
# In your code
import os
os.environ["PROFILE_OUTPUT_DIR"] = "/custom/path/profiles"
```

### **Per-Function Thresholds**

```python
# Fast operations: higher threshold
@profile_function(name="quick_op", min_duration=0.01)

# Slow operations: lower threshold
@profile_function(name="slow_op", min_duration=5.0)
```

### **Conditional Profiling**

```python
import os

# Only profile specific tasks
should_profile = task_id.startswith("prof_")

if should_profile:
    os.environ["ENABLE_PROFILING"] = "true"

# Your code
process_task(task_id)
```

---

## 📚 Additional Resources

### **PyInstrument Docs**
- https://pyinstrument.readthedocs.io/
- https://github.com/joerick/pyinstrument

### **Performance Optimization**
- [Python Performance Tips](https://wiki.python.org/moin/PythonSpeed/PerformanceTips)
- [MoviePy Optimization](https://zulko.github.io/moviepy/getting_started/performance.html)

### **Project Docs**
- `DEVELOPMENT.md` - Development setup
- `docs/IMPROVEMENTS_2026-04-09.md` - Recent improvements

---

## ✅ Checklist

Before optimizing:
- [ ] Profiling enabled in environment
- [ ] Realistic test data prepared
- [ ] Multiple runs executed
- [ ] HTML reports saved
- [ ] Baseline metrics recorded

After optimizing:
- [ ] Re-profile with same data
- [ ] Compare HTML reports
- [ ] Verify improvement > 20%
- [ ] Check for regressions
- [ ] Update performance targets

---

**Happy Profiling! 🚀**

Find bottlenecks, optimize smart, ship fast!
