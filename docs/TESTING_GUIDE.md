# Testing Guide for MoneyPrinterTurbo

**Purpose:** Comprehensive testing strategy for Script Library and other features  
**Date:** April 9, 2026  
**Status:** ✅ Active

---

## 📋 Table of Contents

1. [Running Tests](#running-tests)
2. [Script Storage Tests](#script-storage-tests)
3. [Manual Testing](#manual-testing)
4. [Integration Testing](#integration-testing)
5. [Test Coverage](#test-coverage)
6. [Writing New Tests](#writing-new-tests)

---

## 🚀 Running Tests

### **Setup Test Environment**

```bash
# Install pytest if not already installed
pip install pytest pytest-cov

# Navigate to project root
cd /mnt/data/repos/MoneyPrinterTurbo-openai-tts

# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=webui --cov=app --cov-report=html

# Run specific test file
pytest tests/test_script_storage.py -v

# Run specific test class
pytest tests/test_script_storage.py::TestScriptStorage -v

# Run specific test
pytest tests/test_script_storage.py::TestScriptStorage::test_save_script_returns_id -v
```

### **Test Output**

**Expected successful output:**
```
tests/test_script_storage.py::TestScriptStorage::test_init_creates_directory PASSED
tests/test_script_storage.py::TestScriptStorage::test_save_script_returns_id PASSED
tests/test_script_storage.py::TestScriptStorage::test_save_script_creates_file PASSED
...
======================== 45 passed in 2.34s ========================
```

---

## 🧪 Script Storage Tests

### **Test Coverage**

The `test_script_storage.py` file includes **45 comprehensive tests** covering:

#### **1. Basic Operations (8 tests)**
- ✅ Directory initialization
- ✅ Saving scripts
- ✅ Retrieving scripts
- ✅ File creation
- ✅ Field validation

#### **2. Listing & Filtering (5 tests)**
- ✅ List all scripts
- ✅ Sort by date (newest first)
- ✅ Pagination (limit/offset)
- ✅ Filter by status
- ✅ Multiple status types

#### **3. Update Operations (3 tests)**
- ✅ Update fields
- ✅ Mark as edited
- ✅ Invalid ID handling

#### **4. Delete Operations (3 tests)**
- ✅ Remove file
- ✅ Remove from list
- ✅ Invalid ID handling

#### **5. Script Linking (3 tests)**
- ✅ Mark as used
- ✅ Add task ID
- ✅ Multiple task links

#### **6. Search Functionality (4 tests)**
- ✅ Search by subject
- ✅ Search by keywords
- ✅ Case-insensitive search
- ✅ Search in content

#### **7. Statistics (3 tests)**
- ✅ Total count
- ✅ Count by status
- ✅ Count edited scripts

#### **8. Edge Cases (11 tests)**
- ✅ Empty subject
- ✅ Very long scripts (100KB)
- ✅ Special characters
- ✅ Unicode handling (中文, 日本語, Español)
- ✅ Empty keywords
- ✅ Missing keywords parameter
- ✅ Metadata preservation

#### **9. Error Handling (5 tests)**
- ✅ Invalid script IDs
- ✅ Non-existent files
- ✅ Update failures
- ✅ Delete failures
- ✅ Search errors

---

## 🖱️ Manual Testing

### **Test Case 1: Create and Save Script**

**Objective:** Verify auto-save functionality

**Steps:**
1. Open WebUI
2. Go to **🎬 Create Video** tab
3. Enter subject: "AI in Healthcare"
4. Click **"Generate Script"**
5. Wait for generation to complete

**Expected Results:**
- ✅ Script appears in text area
- ✅ Keywords generated
- ✅ Success message: "Script and keywords generated successfully!"
- ✅ Info message: "Script auto-saved to Script Library"

**Verification:**
1. Go to **📝 Script Library** tab
2. Should see script with subject "AI in Healthcare"
3. Status: Draft
4. Created timestamp should be recent

---

### **Test Case 2: View Script in Library**

**Objective:** Verify script display and details

**Steps:**
1. Go to **📝 Script Library** tab
2. Find your saved script
3. Click to expand card

**Expected Results:**
- ✅ Shows full subject
- ✅ Shows generation timestamp
- ✅ Status indicator (✏️ Draft)
- ✅ Three tabs: Script / Keywords / Actions

**Verification:**
1. Click **Script** tab → Should show full script text
2. Click **Keywords** tab → Should show keyword tags
3. Click **Actions** tab → Should show Create Video / Change Status / Delete buttons

---

### **Test Case 3: Edit Script**

**Objective:** Verify script editing functionality

**Steps:**
1. In Script Library, expand a script card
2. Go to **Script** tab
3. Modify the script text
4. Click **"Save Changes"**

**Expected Results:**
- ✅ Success message: "Script updated successfully"
- ✅ Script reloads with new content
- ✅ Edit indicator (✎) appears on card title

**Verification:**
1. Refresh page
2. Script should still show edited content
3. Edit indicator should persist

---

### **Test Case 4: Create Video from Saved Script**

**Objective:** Verify script-to-task workflow

**Steps:**
1. In Script Library, expand a script
2. Go to **Actions** tab
3. Click **"🎬 Create Video"**
4. Switch to **🎬 Create Video** tab

**Expected Results:**
- ✅ Success message: "Script loaded! Switch to Create Video tab to continue."
- ✅ Video subject filled in
- ✅ Script text populated
- ✅ Keywords populated

**Verification:**
1. Click **"🎬 Create Video Task"**
2. Task should be created
3. Return to **📝 Script Library**
4. Script status should change to **✅ Used**
5. Task ID should appear in "Linked Video Tasks" section

---

### **Test Case 5: Search Scripts**

**Objective:** Verify search functionality

**Steps:**
1. Create multiple scripts with different subjects
2. Go to **📝 Script Library**
3. Enter search term in search box

**Expected Results:**
- ✅ Only matching scripts appear
- ✅ Search is case-insensitive
- ✅ Searches subject, keywords, and content

**Test Searches:**
- "AI" → Should find all AI-related scripts
- "healthcare" → Should find healthcare scripts
- "technology" → Should find scripts with that keyword

---

### **Test Case 6: Filter by Status**

**Objective:** Verify status filtering

**Steps:**
1. Create mix of Draft, Used, and Abandoned scripts
2. Use **"Filter by status"** dropdown

**Expected Results:**
- ✅ "All" → Shows all scripts
- ✅ "Draft" → Shows only drafts
- ✅ "Used" → Shows only scripts linked to tasks
- ✅ "Abandoned" → Shows only abandoned scripts

---

### **Test Case 7: Delete Script**

**Objective:** Verify deletion with confirmation

**Steps:**
1. In Script Library, expand a Draft script
2. Go to **Actions** tab
3. Click **"🗑️ Delete"**
4. Click **"Delete"** again to confirm

**Expected Results:**
- ✅ First click → Warning: "Click Delete again to confirm"
- ✅ Second click → Success: "Script deleted"
- ✅ Script removed from list

**Verification:**
1. Script should not appear in library
2. File should be deleted from disk:
   ```bash
   ls /MoneyPrinterTurbo/storage/scripts/
   # Should not see deleted script_id.json
   ```

---

### **Test Case 8: Statistics Display**

**Objective:** Verify statistics metrics

**Steps:**
1. Create several scripts with different statuses
2. Go to **📝 Script Library**
3. View statistics at top

**Expected Results:**
- ✅ Total Scripts → Correct count
- ✅ Draft → Count of draft scripts
- ✅ Used → Count of scripts linked to tasks
- ✅ Edited → Count of manually edited scripts

---

## 🔗 Integration Testing

### **Test Case 9: Full Workflow End-to-End**

**Objective:** Test complete script-to-video workflow

**Steps:**
1. **Create Script:**
   - Go to Create Video tab
   - Enter subject: "Test Integration"
   - Generate script
   - Verify auto-save message

2. **Verify in Library:**
   - Go to Script Library
   - Find "Test Integration" script
   - Verify status: Draft

3. **Create Video:**
   - In Script Library, click "Create Video"
   - Go to Create Video tab
   - Verify script loaded
   - Create video task

4. **Verify Linking:**
   - Go to Script Library
   - Find script again
   - Status should be: Used
   - Task ID should appear

5. **View Task:**
   - Go to Task Browser
   - Find task by ID
   - Verify it's processing/completed

**Expected Result:**
Complete traceability from script → task → video!

---

### **Test Case 10: Multiple Videos from One Script**

**Objective:** Verify script can be reused

**Steps:**
1. In Script Library, find a Used script
2. Click "Create Video" again
3. Create another video task

**Expected Results:**
- ✅ Script can be reused
- ✅ Multiple task IDs appear in script
- ✅ Both tasks visible in Task Browser

---

## 📊 Test Coverage

### **Running Coverage Report**

```bash
pytest tests/ --cov=webui/services --cov=webui/components --cov-report=html
```

**View coverage:**
```bash
open htmlcov/index.html  # Mac
xdg-open htmlcov/index.html  # Linux
```

### **Target Coverage**

- **Script Storage Service:** 95%+ coverage ✅
- **Script Library Component:** Manual testing (Streamlit UI)
- **Integration Points:** Manual + API testing

---

## ✍️ Writing New Tests

### **Test Template**

```python
"""
Test module for [Feature Name]
"""
import pytest
from [module] import [function]


@pytest.fixture
def sample_data():
    """Provide test data"""
    return {
        "field1": "value1",
        "field2": "value2"
    }


class TestFeatureName:
    """Test suite for FeatureName"""
    
    def test_basic_operation(self, sample_data):
        """Test that basic operation works"""
        result = function(sample_data)
        assert result is not None
    
    def test_edge_case(self):
        """Test edge case handling"""
        result = function(None)
        assert result == expected_value
    
    def test_error_handling(self):
        """Test error is raised correctly"""
        with pytest.raises(ValueError):
            function(invalid_data)
```

### **Best Practices**

1. **One assertion per test** (when possible)
2. **Clear test names** describing what is tested
3. **Use fixtures** for reusable test data
4. **Test both success and failure** cases
5. **Test edge cases** (empty, None, very large)
6. **Clean up** after tests (use fixtures with yield)

---

## 🐛 Debugging Failed Tests

### **View Detailed Output**

```bash
pytest tests/ -v -s  # -s shows print statements
```

### **Run Single Failed Test**

```bash
pytest tests/test_script_storage.py::TestScriptStorage::test_name -v
```

### **Use Debugger**

```python
# Add to test
import pdb; pdb.set_trace()
```

Run with:
```bash
pytest tests/ -v -s  # Debugger will pause at breakpoint
```

---

## ✅ Test Checklist

Before deploying Script Library feature:

- [x] All unit tests pass (45/45)
- [ ] Manual test cases completed (10/10)
- [ ] Integration test completed
- [ ] Coverage > 90%
- [ ] Edge cases tested
- [ ] Error handling verified
- [ ] UI/UX tested in browser
- [ ] Multi-user scenario tested
- [ ] Performance tested (1000+ scripts)
- [ ] Documentation complete

---

## 📝 Test Results Log

### **Latest Test Run**

**Date:** 2026-04-09  
**Tester:** [Your Name]  
**Environment:** Docker containers

| Test Suite | Status | Pass | Fail | Notes |
|------------|--------|------|------|-------|
| Script Storage Unit Tests | ✅ | 45 | 0 | All passing |
| Manual UI Tests | ⏳ | - | - | Pending restart |
| Integration Tests | ⏳ | - | - | Pending restart |

---

## 🎯 Next Steps

1. **Run all unit tests:**
   ```bash
   pytest tests/test_script_storage.py -v
   ```

2. **Restart containers:**
   ```bash
   docker restart moneyprinterturbo-dev-webui
   docker restart moneyprinterturbo-dev-api
   ```

3. **Manual testing:**
   - Complete all 10 manual test cases
   - Document results
   - Report any issues

4. **Integration testing:**
   - Test full workflow
   - Verify task linking
   - Check logs for errors

---

## 📞 Support

**Issues?** Check:
- Test logs: `pytest tests/ -v > test_results.log`
- Container logs: `docker logs moneyprinterturbo-dev-webui`
- Storage directory: `ls /MoneyPrinterTurbo/storage/scripts/`

**Report bugs** with:
- Test name
- Error message
- Steps to reproduce
- Expected vs actual result

---

**Happy Testing! 🧪**
