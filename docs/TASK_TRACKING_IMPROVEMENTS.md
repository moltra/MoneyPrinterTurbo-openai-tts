# Task Tracking & Logging Improvements

**Date:** April 9, 2026  
**Status:** ✅ Implemented

---

## 🎯 Problem Statement

**User Feedback:**
> "Looking at the log file it references clip 23 clip 24. That does not tell me anything. I know we are using a unique task id, but there has to be an easy way that I can tell what sub tasks are part of each task. This is also going to be needed on the Task browser tab."

**Issues Identified:**

1. **No Task Context in Logs**
   - Logs say "processing clip 23" but don't show which task it belongs to
   - Multiple tasks running concurrently → impossible to trace which clip belongs to which video

2. **Missing Clip Details**
   - Only shows "clip 23" but not the filename or what search term it's for
   - No way to correlate failed clips with their source videos

3. **No Task Browser Integration**
   - Task status UI doesn't show detailed progress
   - Can't see what stage each task is in
   - No visibility into which clips are being processed

---

## ✅ Solution: Contextual Logging System

### **1. Task ID Prefix on All Logs**

**Before:**
```
processing clip 23: 1080x1920, current duration: 0.00s...
Failed to process clip 24: /path/to/file.mp4 - 'NoneType' object has no attribute 'value'
```

**After:**
```
[Task: a02f7922-a1a8-44b9-9d64-e311f8d7018f] processing clip 23/30: vid-12345.mp4 (1080x1920), current duration: 0.00s...
[Task: a02f7922-a1a8-44b9-9d64-e311f8d7018f] Failed to process clip 24/30: vid-67890.mp4 - 'NoneType' object has no attribute 'value'
```

### **2. Enhanced Clip Information**

**New Details in Logs:**
- **Clip Number with Total:** `23/30` instead of just `23`
- **Filename:** Shows actual filename instead of full path
- **Task Association:** Every log line prefixed with `[Task: {task_id}]`

### **3. Detailed Failure Summary**

**Before:**
```
Clip processing summary: 3 failed out of 30 (10.0%)
```

**After:**
```
[Task: a02f7922] Clip processing summary: 3 failed out of 30 (10.0%)
[Task: a02f7922]   - Clip 23: vid-f8908b12.mp4 - 'NoneType' object has no attribute 'value'
[Task: a02f7922]   - Clip 24: vid-8d1f3f5d.mp4 - 'NoneType' object has no attribute 'value'
[Task: a02f7922]   - Clip 25: vid-f8908b12.mp4 - 'NoneType' object has no attribute 'value'
```

---

## 📋 Files Modified

### **1. `app/services/video.py`**

**Changes:**
- Added `task_id: str = None` parameter to `combine_videos()`
- Created `log_prefix` variable: `f"[Task: {task_id}] "` if task_id else `""`
- Added task prefix to all logger calls
- Enhanced clip filenames (basename instead of full path)
- Added clip count (`23/30`)
- Added detailed failure summary with per-clip breakdown

**Key Functions:**
```python
def combine_videos(
    ...
    task_id: str = None,  # ← NEW
) -> str:
    log_prefix = f"[Task: {task_id}] " if task_id else ""
    
    logger.info(f"{log_prefix}audio duration: {audio_duration} seconds")
    logger.debug(f"{log_prefix}processing clip {i+1}/{len(subclipped_items)}: {clip_filename}...")
    logger.error(f"{log_prefix}Failed to process clip {i+1}/{len(subclipped_items)}: {clip_filename} - {str(e)}")
```

### **2. `app/services/task.py`**

**Changes:**
- Added `task_id` parameter to `combine_videos()` call
- Added `[Task: {task_id}]` prefix to all task-level logs
- Updated `generate_script()`, `generate_terms()`, `generate_sentence_terms()`

**Example:**
```python
def generate_script(task_id, params):
    logger.info(f"[Task: {task_id}] \n\n## generating video script")
    # ...
    logger.error(f"[Task: {task_id}] failed to generate video script.")
```

---

## 🔍 Log Analysis Examples

### **Example 1: Single Task Tracking**

**Search for all logs for a specific task:**
```bash
docker logs moneyprinterturbo-dev-api | grep "a02f7922"
```

**Output:**
```
[Task: a02f7922] ## generating video script
[Task: a02f7922] ## generating video terms
[Task: a02f7922] audio duration: 30.96 seconds
[Task: a02f7922] maximum clip duration: 5 seconds
[Task: a02f7922] total subclipped items: 30
[Task: a02f7922] processing clip 1/30: vid-abc123.mp4 (1080x1920)...
[Task: a02f7922] processing clip 2/30: vid-def456.mp4 (1080x1920)...
...
[Task: a02f7922] video duration: 30.96s, audio duration: 30.96s
```

### **Example 2: Multi-Task Concurrent Processing**

**Log Output with 3 tasks running:**
```
[Task: a02f7922] processing clip 5/30: vid-abc.mp4...
[Task: 8920c410] processing clip 12/25: vid-xyz.mp4...
[Task: e3be4598] ## generating video terms
[Task: a02f7922] processing clip 6/30: vid-def.mp4...
[Task: 8920c410] processing clip 13/25: vid-123.mp4...
[Task: a02f7922] Failed to process clip 7/30: vid-ghi.mp4 - error message
```

Now you can **easily filter by task ID**!

### **Example 3: Find All Failed Clips**

```bash
docker logs moneyprinterturbo-dev-api | grep "Failed to process clip"
```

**Output:**
```
[Task: a02f7922] Failed to process clip 23/30: vid-f8908b12.mp4 - 'NoneType' object has no attribute 'value'
[Task: a02f7922] Failed to process clip 24/30: vid-8d1f3f5d.mp4 - 'NoneType' object has no attribute 'value'
[Task: 8920c410] Failed to process clip 15/25: vid-abc123.mp4 - Connection timeout
```

---

## 🎨 Future Enhancements (Task Browser)

### **Proposed UI Improvements:**

#### **1. Task List View**
```
╔════════════════════════════════════════════════════════════════╗
║ Task ID          | Status      | Progress | Details           ║
╠════════════════════════════════════════════════════════════════╣
║ a02f7922-a1a8... | Processing  | 65%      | Combining clips   ║
║                  |             |          | 23/30 clips done  ║
╠════════════════════════════════════════════════════════════════╣
║ 8920c410-827f... | Completed   | 100%     | Video ready       ║
╠════════════════════════════════════════════════════════════════╣
║ e3be4598-b5c3... | Failed      | 45%      | Too many errors   ║
║                  |             |          | 15/30 clips failed║
╚════════════════════════════════════════════════════════════════╝
```

#### **2. Task Detail View**

When clicking on a task:
```
Task: a02f7922-a1a8-44b9-9d64-e311f8d7018f
Subject: home improvement
Status: Processing (65%)

Timeline:
  ✅ Script Generated      [12:48:00]
  ✅ Terms Generated       [12:48:05]
  ⏳ Video Processing      [12:48:10] (current)
     - Clip 1/30: vid-abc.mp4 ✅
     - Clip 2/30: vid-def.mp4 ✅
     ...
     - Clip 23/30: vid-ghi.mp4 ❌ 'NoneType' error
     - Clip 24/30: vid-jkl.mp4 ⏳ Processing...
  ⏸️ Subtitle Generation   [pending]
  ⏸️ Final Assembly        [pending]

Failed Clips (3):
  • Clip 23: vid-f8908b12.mp4
    Error: 'NoneType' object has no attribute 'value'
  • Clip 24: vid-8d1f3f5d.mp4
    Error: 'NoneType' object has no attribute 'value'
  • Clip 25: vid-f8908b12.mp4
    Error: 'NoneType' object has no attribute 'value'

[View Full Logs] [Download Video] [Retry Failed Clips]
```

#### **3. Real-Time Log Streaming**

```python
# In WebUI components/task_browser.py
def render_task_logs(task_id: str):
    """Stream logs for a specific task in real-time"""
    st.subheader(f"Task Logs: {task_id[:8]}...")
    
    # Filter logs by task_id
    log_url = f"{api_base}/api/v1/tasks/{task_id}/logs"
    response = requests.get(log_url, stream=True)
    
    log_container = st.empty()
    for line in response.iter_lines():
        if line:
            log_container.text_area("Logs", value=line.decode(), height=400)
```

---

## 📊 Benefits

### **For Developers:**
- ✅ **Easy debugging** - Filter logs by task ID
- ✅ **Concurrent task tracking** - See multiple tasks clearly
- ✅ **Root cause analysis** - Know exactly which clip failed and why

### **For Users:**
- ✅ **Transparency** - See what's happening with their video
- ✅ **Progress tracking** - Know how many clips are processed
- ✅ **Error understanding** - Clear failure messages with context

### **For Operations:**
- ✅ **Performance monitoring** - Track task completion rates
- ✅ **Failure analysis** - Identify problematic video sources
- ✅ **Capacity planning** - See concurrent task loads

---

## 🚀 Deployment

**1. Restart API Container:**
```bash
docker restart moneyprinterturbo-dev-api
```

**2. Test with New Task:**
```bash
# Create a video task
# Check logs with:
docker logs -f moneyprinterturbo-dev-api | grep "Task:"
```

**3. Verify Improved Logging:**
- ✅ All logs show `[Task: {uuid}]` prefix
- ✅ Clip numbers show `X/Y` format
- ✅ Filenames shown instead of full paths
- ✅ Detailed failure summaries at the end

---

## 📝 Quick Reference

### **Log Filtering Commands:**

```bash
# View all logs for a specific task
docker logs moneyprinterturbo-dev-api | grep "[Task: a02f7922]"

# View only failed clips
docker logs moneyprinterturbo-dev-api | grep "Failed to process clip"

# View task lifecycle (script → terms → video)
docker logs moneyprinterturbo-dev-api | grep -E "(generating video script|generating video terms|combining video)"

# Real-time monitoring of all tasks
docker logs -f moneyprinterturbo-dev-api | grep -E "\[Task:"

# Count failures per task
docker logs moneyprinterturbo-dev-api | grep "Clip processing summary"
```

### **Task ID Format:**

UUID v4: `a02f7922-a1a8-44b9-9d64-e311f8d7018f`
- First 8 chars often used for short reference: `a02f7922`
- Full UUID for precise filtering

---

## ✅ Verification Checklist

After deploying:

- [ ] Logs include `[Task: {uuid}]` prefix
- [ ] Clip numbers show as `X/Y` (e.g., `23/30`)
- [ ] Filenames displayed (not full paths)
- [ ] Failed clips list shown with details
- [ ] Can filter logs by task ID
- [ ] Multiple concurrent tasks are distinguishable

---

## 🎉 Summary

**Before:** Cryptic logs with no context  
**After:** Rich, traceable logs with task IDs, clip details, and failure summaries

**Result:** Easy debugging, better user visibility, production-ready logging! 🚀
