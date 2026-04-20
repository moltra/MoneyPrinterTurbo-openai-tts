# PyInstrument Profiling - Quick Start

**5-minute guide to finding performance bottlenecks**

---

## 🚀 Enable Profiling

```bash
# In docker-compose.yml
services:
  api:
    environment:
      - ENABLE_PROFILING=true
```

```bash
# Restart
docker restart moneyprinterturbo-dev-api
```

---

## 📊 Already Profiled

These functions are already instrumented:

### **Video Processing** (1s+ threshold)
- `combine_videos()` - Video concatenation & effects

### **LLM Calls** (0.5s+ threshold)
- `generate_script()` - Script generation
- `generate_terms()` - Keyword generation

---

## 🔧 Add Profiling to Your Code

### **Method 1: Decorator** (Easiest)

```python
from app.utils.profiling import profile_function

@profile_function(name="my_function", save_html=True, min_duration=0.5)
def expensive_function(data):
    # Your code
    return result
```

### **Method 2: Context Manager** (Flexible)

```python
from app.utils.profiling import ProfileContext

def my_function():
    with ProfileContext("slow_part", save_html=True) as p:
        # Code to profile
        result = expensive_operation()
    
    print(f"Took: {p.duration:.3f}s")
    return result
```

### **Method 3: Manual** (Most Control)

```python
from app.utils.profiling import start_profile, stop_profile

def my_function():
    profiler = start_profile("operation")
    
    # Your code here
    result = do_work()
    
    stop_profile(profiler, "operation", save_html=True)
    return result
```

---

## 📈 View Results

### **In Logs**

```bash
docker logs -f moneyprinterturbo-dev-api | grep "Profile:"
```

**Output:**
```
⏱️  Profile: combine_videos took 12.345s
⏱️  Profile: generate_script took 2.456s
```

### **HTML Reports**

```bash
# Copy reports
docker cp moneyprinterturbo-dev-api:/MoneyPrinterTurbo/storage/profiles ./profiles

# Open in browser
open profiles/combine_videos_*.html
```

---

## 🎯 Quick Wins

### **Find Bottlenecks**

1. Look for functions taking > 1s
2. Check if called multiple times
3. Focus on highest total time

### **Common Fixes**

```python
# ❌ Slow: Sequential processing
for item in items:
    process(item)

# ✅ Fast: Batch processing
process_batch(items)

# ❌ Slow: Multiple API calls
for id in ids:
    fetch(id)

# ✅ Fast: Single batch call
fetch_all(ids)

# ❌ Slow: Re-reading same file
for i in range(100):
    data = read_file("config.json")

# ✅ Fast: Read once
data = read_file("config.json")
for i in range(100):
    use(data)
```

---

## 📝 Example: Profile API Call

```python
from pyinstrument import Profiler

def fetch_tasks(api_url):
    profiler = Profiler()
    profiler.start()
    
    response = requests.get(api_url)
    data = response.json()
    
    profiler.stop()
    
    if profiler.last_session.duration > 0.1:
        print(f"⏱️  API call took {profiler.last_session.duration:.3f}s")
        print(profiler.output_text(unicode=True, color=True))
    
    return data
```

---

## ⚙️ Configuration

### **Environment Variables**

```bash
ENABLE_PROFILING=true          # Enable/disable
PROFILE_MIN_DURATION=0.1       # Min time to log (seconds)
PROFILE_OUTPUT_DIR=/path/      # HTML report directory
```

### **Decorator Parameters**

```python
@profile_function(
    name="custom_name",        # Profile name
    save_html=True,            # Save HTML report
    print_results=True,        # Print to logs
    min_duration=0.5           # Only log if > 0.5s
)
```

---

## 🎓 Learn More

- **Full Guide:** `docs/PYINSTRUMENT_PROFILING_GUIDE.md`
- **Examples:** `examples/profiling_examples.py`
- **PyInstrument Docs:** https://pyinstrument.readthedocs.io/

---

## ✅ Checklist

- [ ] Enable profiling in docker-compose
- [ ] Restart containers
- [ ] Run operation to profile
- [ ] Check logs for "Profile:" messages
- [ ] Copy HTML reports to local
- [ ] Analyze bottlenecks
- [ ] Optimize high-impact areas
- [ ] Re-profile to verify improvement

---

**Ready to optimize! 🚀**
