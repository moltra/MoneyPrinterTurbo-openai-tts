# Test Suite for MoneyPrinterTurbo

This directory contains automated tests for the MoneyPrinterTurbo application.

## 🚀 Quick Start

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test File
```bash
pytest tests/test_script_storage.py -v
```

### Run with Coverage
```bash
pytest tests/ -v --cov=webui --cov=app --cov-report=html
```

## 📋 Available Tests

### Script Storage Tests (45 tests)
**File:** `test_script_storage.py`  
**Coverage:** Script persistence, search, filtering, linking

```bash
pytest tests/test_script_storage.py -v
```

**Test Classes:**
- `TestScriptStorage` - Core functionality (32 tests)
- `TestScriptStorageEdgeCases` - Edge cases (13 tests)

## 📊 Expected Output

**Success:**
```
tests/test_script_storage.py::TestScriptStorage::test_init_creates_directory PASSED
tests/test_script_storage.py::TestScriptStorage::test_save_script_returns_id PASSED
...
======================== 45 passed in 2.34s ========================
```

**With Coverage:**
```
Name                                    Stmts   Miss  Cover
-----------------------------------------------------------
webui/services/script_storage.py          248     12    95%
-----------------------------------------------------------
TOTAL                                     248     12    95%
```

## 🧪 Test Categories

1. **Basic Operations** (8 tests)
   - Initialization
   - Save/Get/Update/Delete

2. **Listing & Filtering** (5 tests)
   - Pagination
   - Status filtering
   - Sorting

3. **Search** (4 tests)
   - By subject
   - By keywords
   - Case-insensitive

4. **Linking** (3 tests)
   - Mark as used
   - Multiple tasks

5. **Statistics** (3 tests)
   - Total count
   - By status
   - Edited count

6. **Edge Cases** (11 tests)
   - Empty values
   - Very long content
   - Unicode characters

7. **Error Handling** (5 tests)
   - Invalid IDs
   - Missing files

## 🔧 Requirements

```bash
pip install pytest pytest-cov
```

## 📖 Documentation

See `docs/TESTING_GUIDE.md` for comprehensive testing guide including:
- Manual test cases
- Integration testing
- Writing new tests
- Debugging tips

## ✅ Pre-Deployment Checklist

Before deploying new features:

- [ ] All unit tests pass
- [ ] Coverage > 90%
- [ ] Manual tests completed
- [ ] Integration tests pass
- [ ] Documentation updated

## 🐛 Debugging

**View detailed output:**
```bash
pytest tests/ -v -s
```

**Run single test:**
```bash
pytest tests/test_script_storage.py::TestScriptStorage::test_name -v
```

**Use debugger:**
```python
# Add to test
import pdb; pdb.set_trace()
```

## 📞 Help

**Common Issues:**

1. **Import errors:** Make sure you're in project root
2. **Permission errors:** Check storage directory permissions
3. **Test failures:** Read error messages carefully

**Need help?** Check `docs/TESTING_GUIDE.md`

---

**Happy Testing! 🎉**
