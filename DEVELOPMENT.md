# Development Guide

**MoneyPrinterTurbo Development Setup & Best Practices**

---

## 🚀 Quick Start

### **1. Install Dependencies**

```bash
# Production dependencies
pip install -r requirements.txt

# Development dependencies (formatters, linters, tests)
pip install -r requirements-dev.txt
```

### **2. Development Workflow**

```bash
# Format code before committing
make format

# Lint code
make lint

# Run tests
make test

# All-in-one (format + lint + test)
make all
```

---

## 🛠️ Development Tools

### **Code Formatting & Linting**

#### **Ruff** - Fast Python linter
```bash
# Check all code
ruff check app/ webui/ tests/

# Auto-fix issues
ruff check --fix app/ webui/ tests/

# Watch mode
ruff check --watch app/ webui/
```

#### **Black** - Code formatter
```bash
# Format code
black app/ webui/ tests/

# Check formatting
black --check app/ webui/
```

#### **isort** - Import sorter
```bash
# Sort imports
isort app/ webui/ tests/

# Check import sorting
isort --check-only app/ webui/
```

### **Using Makefile Commands**

```bash
make help          # Show all commands
make install       # Install production deps
make install-dev   # Install dev deps
make format        # Format code (black + isort)
make lint          # Lint code (ruff)
make lint-fix      # Auto-fix lint issues
make test          # Run tests
make test-cov      # Run tests with coverage
make clean         # Remove cache files
make all           # Format + Lint + Test
```

---

## 🧪 Testing

### **Run Tests**

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_script_storage.py -v

# Specific test
pytest tests/test_script_storage.py::TestScriptStorage::test_save_script -v

# With coverage
pytest tests/ --cov=app --cov=webui --cov-report=html

# View coverage report
open htmlcov/index.html  # Mac
xdg-open htmlcov/index.html  # Linux
```

### **Writing Tests**

```python
# tests/test_example.py
import pytest

@pytest.fixture
def sample_data():
    """Reusable test data"""
    return {"key": "value"}

def test_example(sample_data):
    """Test description"""
    assert sample_data["key"] == "value"
```

---

## 📊 Performance Profiling

### **PyInstrument** - Profile code

```python
from pyinstrument import Profiler

profiler = Profiler()
profiler.start()

# Code to profile
result = expensive_function()

profiler.stop()
profiler.print()

# Save to HTML
with open('profile.html', 'w') as f:
    f.write(profiler.output_html())
```

### **Profile Endpoints**

```python
# In FastAPI endpoint
from pyinstrument import Profiler

@app.post("/api/v1/videos")
async def create_video(params: VideoParams):
    profiler = Profiler()
    profiler.start()
    
    result = await process_video(params)
    
    profiler.stop()
    logger.info(profiler.output_text(unicode=True, color=True))
    
    return result
```

---

## 🔄 Retry Logic with Tenacity

### **Basic Retry**

```python
from tenacity import retry, stop_after_attempt

@retry(stop=stop_after_attempt(3))
def flaky_function():
    # Automatically retries up to 3 times
    return requests.get("https://api.example.com")
```

### **Exponential Backoff**

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def api_call_with_backoff():
    # Retries with increasing delays: 2s, 4s, 8s, 10s, 10s
    return requests.post(...)
```

### **Retry on Specific Exceptions**

```python
from tenacity import retry, retry_if_exception_type, stop_after_attempt

@retry(
    retry=retry_if_exception_type(ConnectionError),
    stop=stop_after_attempt(3)
)
def network_operation():
    # Only retries on ConnectionError
    return requests.get(...)
```

---

## 🗄️ Database (SQLite)

### **Query Database**

```bash
# Connect to database
sqlite3 /MoneyPrinterTurbo/storage/scripts.db

# Or in Docker
docker exec -it moneyprinterturbo-dev-webui sqlite3 /MoneyPrinterTurbo/storage/scripts.db
```

```sql
-- List all tables
.tables

-- Schema
.schema scripts

-- Count scripts
SELECT COUNT(*) FROM scripts;

-- View recent scripts
SELECT script_id, subject, status, generated_at 
FROM scripts 
ORDER BY generated_at DESC 
LIMIT 10;

-- Search
SELECT * FROM scripts_fts WHERE scripts_fts MATCH 'AI healthcare';

-- Statistics
SELECT status, COUNT(*) as count 
FROM scripts 
GROUP BY status;
```

### **Backup Database**

```bash
# Backup with timestamp
timestamp=$(date +%Y%m%d_%H%M%S)
docker cp moneyprinterturbo-dev-webui:/MoneyPrinterTurbo/storage/scripts.db ./scripts_backup_$timestamp.db
```

---

## 🎨 Code Style Guidelines

### **Python Style**

- **Line length:** 120 characters
- **Quotes:** Double quotes for strings
- **Imports:** Sorted with isort
- **Formatting:** Black style
- **Linting:** Ruff rules

### **Naming Conventions**

```python
# Variables & functions: snake_case
user_name = "Alice"
def calculate_total(): pass

# Classes: PascalCase
class ScriptStorage: pass

# Constants: UPPER_SNAKE_CASE
MAX_RETRIES = 3
API_TIMEOUT = 30

# Private: Leading underscore
def _internal_helper(): pass
_private_var = 42
```

### **Type Hints**

```python
from typing import List, Dict, Optional

def process_scripts(
    scripts: List[Dict[str, Any]],
    limit: int = 100,
    offset: Optional[int] = None
) -> List[str]:
    """Process scripts and return IDs"""
    return [s["script_id"] for s in scripts]
```

---

## 🐛 Debugging

### **Logging**

```python
from loguru import logger

# Different levels
logger.debug("Debug info")
logger.info("Normal operation")
logger.warning("Something unusual")
logger.error("Error occurred")
logger.success("Operation successful")

# With context
logger.info(f"Processing script: {script_id}")
logger.error(f"Failed to save script: {e}", exc_info=True)
```

### **Debug in Container**

```bash
# View logs
docker logs -f moneyprinterturbo-dev-webui
docker logs -f moneyprinterturbo-dev-api

# Exec into container
docker exec -it moneyprinterturbo-dev-webui bash

# Python REPL in container
docker exec -it moneyprinterturbo-dev-webui python

# Run script in container
docker exec moneyprinterturbo-dev-webui python scripts/test_script.py
```

### **Breakpoints**

```python
# Add breakpoint
breakpoint()  # Python 3.7+

# Or
import pdb; pdb.set_trace()

# Commands in debugger:
# n - next line
# s - step into
# c - continue
# p variable - print variable
# l - list code
# q - quit
```

---

## 🔧 Configuration

### **Environment Variables**

```bash
# .env file or docker-compose.yml
USE_SQLITE_STORAGE=true
LOG_LEVEL=DEBUG
PYTHONUNBUFFERED=1
```

### **Config Files**

- `ruff.toml` - Ruff configuration
- `pyproject.toml` - Black, isort, pytest, mypy config
- `requirements.txt` - Production dependencies
- `requirements-dev.txt` - Development dependencies

---

## 📝 Git Workflow

### **Before Committing**

```bash
# Format & lint
make format
make lint

# Run tests
make test

# Check all
make all
```

### **Commit Messages**

```
feat: Add SQLite storage backend
fix: Fix nested expander bug in task browser
docs: Update migration guide
test: Add tests for script search
refactor: Simplify script storage API
perf: Optimize video processing
```

---

## 🚢 Docker Development

### **Rebuild Containers**

```bash
# Rebuild WebUI
docker-compose -f moneyprinterturbo-dev-clean.yml build webui
docker-compose -f moneyprinterturbo-dev-clean.yml up -d webui

# Rebuild API
docker-compose -f moneyprinterturbo-dev-clean.yml build api
docker-compose -f moneyprinterturbo-dev-clean.yml up -d api
```

### **View Container Resources**

```bash
# CPU/Memory usage
docker stats moneyprinterturbo-dev-webui moneyprinterturbo-dev-api

# Disk usage
docker system df

# Clean up
docker system prune -a
```

---

## 📚 Resources

### **Documentation**

- [Ruff Docs](https://docs.astral.sh/ruff/)
- [Black Docs](https://black.readthedocs.io/)
- [Pytest Docs](https://docs.pytest.org/)
- [Tenacity Docs](https://tenacity.readthedocs.io/)
- [SQLite FTS5](https://www.sqlite.org/fts5.html)

### **Project Docs**

- `docs/SQLITE_MIGRATION.md` - SQLite migration guide
- `docs/TESTING_GUIDE.md` - Testing procedures
- `docs/SCRIPT_LIBRARY.md` - Script Library feature
- `docs/TASK_BROWSER_IMPLEMENTATION.md` - Task Browser

---

## ✅ Development Checklist

Before submitting changes:

- [ ] Code formatted (black + isort)
- [ ] Linting passes (ruff)
- [ ] All tests pass
- [ ] Coverage > 90%
- [ ] Documentation updated
- [ ] Migration script tested (if schema changed)
- [ ] Tested in Docker containers
- [ ] No debug print statements
- [ ] Proper error handling
- [ ] Logging added for important operations

---

**Happy Coding! 🚀**
