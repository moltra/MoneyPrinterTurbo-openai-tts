# Ollama Model Memory Management

**Feature:** Configurable model keep-alive and unload behavior  
**Date:** April 9, 2026

---

## 🎯 Overview

Control how long Ollama models stay loaded in memory after generation. This affects:
- **Speed:** Loaded models respond instantly
- **RAM usage:** Unloaded models free up memory
- **First request latency:** Loading from disk takes 20-30 seconds

---

## ⚙️ Configuration Options

### **1. Keep Alive Minutes**
**Config key:** `ollama_keep_alive_minutes`

| Value | Behavior | Speed | RAM Usage | Use Case |
|-------|----------|-------|-----------|----------|
| **-1** | Keep forever | ⚡ Fastest | 🔴 High | Dedicated server, frequent use |
| **5** | Keep 5 min (default) | ✅ Balanced | 🟡 Medium | General use, occasional generation |
| **0** | Unload immediately | 🐌 Slowest | 🟢 Low | Shared server, infrequent use |

**Default:** `5` minutes

### **2. Force Unload After Generate**
**Config key:** `ollama_unload_after_generate`

| Value | Behavior |
|-------|----------|
| **false** (default) | Use keep-alive timer |
| **true** | Force unload after EVERY generation |

⚠️ **Warning:** Setting to `true` makes the model reload for every single request (very slow!)

---

## 📋 How It Works

### **Normal Flow (keep_alive_minutes = 5)**
```
Request 1: Load model (22s) + Generate (10s) = 32s
           ↓
        [Model stays in RAM for 5 minutes]
           ↓
Request 2: Generate (10s) = 10s ⚡ (already loaded!)
Request 3: Generate (10s) = 10s ⚡
           ↓
        [After 5 minutes of inactivity]
           ↓
        Model automatically unloads
           ↓
Request 4: Load model (22s) + Generate (10s) = 32s
```

### **Forever Mode (keep_alive_minutes = -1)**
```
Request 1: Load model (22s) + Generate (10s) = 32s
           ↓
        [Model NEVER unloads]
           ↓
Request 2+: Generate (10s) = 10s ⚡ ALWAYS instant!
```

### **Immediate Unload (keep_alive_minutes = 0)**
```
Every Request: Load (22s) + Generate (10s) + Unload = 32s
               [Model unloads immediately after generation]
```

---

## 🖥️ WebUI Configuration

### **Location:**
1. Go to **⚙️ Config** tab
2. Select **LLM Provider** sub-tab
3. Choose **Ollama** as provider
4. Scroll to **Model Memory Management** section

### **UI Controls:**

```
┌───────────────────────────────────────────────────────┐
│ Model Memory Management                                │
├──────────────────────────┬────────────────────────────┤
│ Keep Model in Memory     │ Force Unload After         │
│ (minutes)                │ Generation                 │
│                          │                            │
│ [-1] [+] [5]            │ [ ] Force unload           │
│                          │                            │
│ ⏱️ Model stays loaded for│ 💡 Model stays loaded      │
│ 5 minutes                │ based on keep-alive timer  │
│                          │ (recommended)              │
└──────────────────────────┴────────────────────────────┘
```

### **Options:**

**Keep Model in Memory (minutes):**
- Use number input to set: `-1` to `120`
- `-1` = ♾️ Forever (fastest)
- `0` = ⚡ Immediate unload (lowest RAM)
- `5` = ⏱️ Default (balanced)

**Force Unload checkbox:**
- Unchecked (default) = Use timer ✅
- Checked = Unload after every request ⚠️

---

## 🔧 Technical Details

### **Code Location:**
- **Config:** `config.toml` (lines 60-64)
- **Backend:** `app/services/llm.py` (function `unload_ollama_model`)
- **WebUI:** `webui/components/llm_config.py` (lines 371-407)

### **How Keep-Alive Works:**

When a generation completes, the system calls:
```python
unload_ollama_model(model_name)
```

This function:
1. Reads `ollama_keep_alive_minutes` from config
2. Converts to Ollama's format:
   - `-1` → `-1` (never unload)
   - `0` → `0` (unload now)
   - `5` → `"5m"` (keep 5 minutes)
3. Sends to Ollama API:
   ```json
   {
     "model": "bjoernb/gemma4-e4b-think:latest",
     "keep_alive": "5m"
   }
   ```

### **Ollama Keep-Alive Format:**
- `0` = Unload immediately
- `"5m"` = Keep 5 minutes
- `"1h"` = Keep 1 hour
- `-1` = Keep forever

---

## 💡 Recommendations

### **For Your Setup (Dedicated Server, GPU)**
**Recommended:** `ollama_keep_alive_minutes = -1`

**Reasons:**
- ✅ You have dedicated GPU with 3.2GB VRAM
- ✅ Model is only 9.9GB (fits comfortably)
- ✅ No need to share resources
- ✅ Instant responses for all requests
- ✅ No 22-second load delays

**Configuration:**
```toml
[app]
ollama_keep_alive_minutes = -1
ollama_unload_after_generate = false
```

### **For Shared Servers**
**Recommended:** `ollama_keep_alive_minutes = 5`

**Reasons:**
- Multiple users/services
- Need to free RAM when idle
- Balanced performance

### **For RAM-Constrained Systems**
**Recommended:** `ollama_keep_alive_minutes = 0`

**Reasons:**
- Limited RAM available
- Infrequent use
- Can tolerate 20-30s load time

---

## 📊 Performance Comparison

### **Your Model:** `bjoernb/gemma4-e4b-think:latest`

| Keep-Alive | First Request | Subsequent Requests | RAM After 5min Idle |
|------------|---------------|---------------------|---------------------|
| **-1** (Forever) | 32s | **10s** ⚡ | 9.9 GB (always loaded) |
| **5** (Default) | 32s | **10s** ⚡ | 0 GB (unloaded) |
| **0** (Immediate) | 32s | **32s** 🐌 | 0 GB (always unloaded) |

### **Sentence-Level Generation (8 sentences)**

| Keep-Alive | Total Time | Notes |
|------------|------------|-------|
| **-1** | ~100s | Load once, then instant ⚡ |
| **5** | ~100s | Same (within 5min window) |
| **0** | ~320s | Loads 9 times! (script + 8 sentences) 😱 |

---

## 🚀 Quick Start

### **Step 1: Navigate to Config**
1. Open WebUI
2. Click **⚙️ Config** tab
3. Select **LLM Provider** sub-tab

### **Step 2: Configure**
1. Scroll to **Model Memory Management**
2. Set **Keep Model in Memory** to `-1` (forever)
3. Leave **Force Unload** unchecked
4. Click **💾 Save Configuration**

### **Step 3: Restart API**
```bash
docker restart moneyprinterturbo-dev-api
```

### **Step 4: Verify**
Check Ollama logs after generation:
```
ollama model keep_alive set to: -1
```

---

## 🔍 Troubleshooting

### **Model Still Unloading?**

**Check 1:** Config saved?
```bash
cat /home/mark/docker/appdata/moneyprinterturbo-dev/config/config.toml | grep keep_alive
```

Expected output:
```toml
ollama_keep_alive_minutes = -1
```

**Check 2:** API restarted after config change?
```bash
docker restart moneyprinterturbo-dev-api
```

**Check 3:** Logs showing correct setting?
```bash
docker logs moneyprinterturbo-dev-api --tail 100 | grep keep_alive
```

Expected:
```
ollama model keep_alive set to: -1
```

### **Model Loading Slowly?**

This is normal on first request:
- **Model load:** ~22 seconds (loading 9.9GB into VRAM)
- **Generation:** ~10-30 seconds
- **Total first time:** ~32-52 seconds

With `keep_alive = -1`, subsequent requests are instant!

---

## 📈 Monitoring

### **Check Ollama Model Status:**
```bash
curl http://192.168.0.116:11436/api/tags
```

Shows loaded models with their keep-alive status.

### **Check Memory Usage:**
```bash
docker stats ollama
```

Shows RAM and GPU memory used by Ollama.

---

## 🎯 Summary

- ✅ **Configurable keep-alive** replaces hardcoded `0`
- ✅ **WebUI controls** for easy adjustment
- ✅ **Recommended: `-1` (forever)** for your dedicated GPU setup
- ✅ **Saves 20-30 seconds** on every generation after the first
- ✅ **No more timeout issues** with sentence-level generation

**Result:** Instant AI responses after initial model load! 🚀
