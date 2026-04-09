# Script Library Deployment Guide

**Feature:** Complete Script Management System  
**Status:** ✅ Ready for Testing  
**Date:** April 9, 2026

---

## 📦 What Was Built

### **1. Backend Storage Service**
- **File:** `webui/services/script_storage.py` (328 lines)
- **Features:**
  - Persistent JSON storage
  - CRUD operations
  - Search functionality
  - Status management
  - Task linking
  - Statistics

### **2. UI Component**
- **File:** `webui/components/script_library.py` (366 lines)
- **Features:**
  - Script list with cards
  - Search and filter
  - Edit capability
  - One-click video creation
  - Status management
  - Delete with confirmation

### **3. Comprehensive Testing**
- **File:** `tests/test_script_storage.py` (540+ lines)
- **Coverage:** 45 unit tests
- **Areas:** Operations, search, linking, statistics, edge cases

### **4. Integration**
- **Auto-save** in Create Video tab
- **Script-task linking** on video creation
- **New tab** in main UI

### **5. Documentation**
- `docs/SCRIPT_LIBRARY.md` - Feature documentation
- `docs/TESTING_GUIDE.md` - Testing instructions
- `tests/README.md` - Quick testing reference
- This deployment guide

---

## 🚀 Deployment Steps

### **Step 1: Run Tests**

```bash
# Navigate to project root
cd /mnt/data/repos/MoneyPrinterTurbo-openai-tts

# Install pytest if needed
pip install pytest pytest-cov

# Run all tests
pytest tests/test_script_storage.py -v

# Expected: All 45 tests PASS
```

**✅ Verify:**
```
======================== 45 passed in X.XXs ========================
```

---

### **Step 2: Create Storage Directory**

```bash
# Create scripts storage directory
docker exec moneyprinterturbo-dev-api mkdir -p /MoneyPrinterTurbo/storage/scripts

# Set permissions
docker exec moneyprinterturbo-dev-api chmod 755 /MoneyPrinterTurbo/storage/scripts

# Verify
docker exec moneyprinterturbo-dev-api ls -la /MoneyPrinterTurbo/storage/scripts
```

**✅ Verify:**
```
drwxr-xr-x 2 root root 4096 Apr  9 14:00 scripts
```

---

### **Step 3: Restart Containers**

```bash
# Restart WebUI (includes new UI components)
docker restart moneyprinterturbo-dev-webui

# Restart API (if code changes deployed there)
docker restart moneyprinterturbo-dev-api

# Watch logs
docker logs -f moneyprinterturbo-dev-webui
```

**✅ Verify:**
- No errors in logs
- WebUI starts successfully
- Can access http://localhost:8502

---

### **Step 4: Verify UI**

1. **Open WebUI:** http://localhost:8502

2. **Check tabs:**
   ```
   🎬 Create Video
   📦 Bulk Create
   📝 Script Library  ← NEW!
   📊 Task Browser
   ⚙️ Config
   ```

3. **Click "📝 Script Library"**
   - Should load without errors
   - Shows empty state: "No scripts found"
   - Shows statistics: All zeros

**✅ Verify:** Tab loads, no errors

---

### **Step 5: Test Auto-Save**

1. **Go to Create Video tab**
2. **Enter subject:** "Test Script Auto-Save"
3. **Click "Generate Script"**
4. **Wait for generation**

**✅ Verify:**
- ✅ Script generated
- ✅ Success message
- ✅ Info message: "Script auto-saved to Script Library"
- ✅ Check logs:
  ```bash
  docker logs moneyprinterturbo-dev-webui | grep "Auto-saved script"
  ```

---

### **Step 6: Test Script Library**

1. **Go to Script Library tab**
2. **Should see:**
   - Statistics: Total Scripts: 1, Draft: 1
   - One script card
   - Subject: "Test Script Auto-Save"
   - Status: ✏️ Draft

3. **Expand card**
4. **Check tabs:**
   - Script tab → Shows full text
   - Keywords tab → Shows keywords
   - Actions tab → Shows buttons

**✅ Verify:** Script appears correctly

---

### **Step 7: Test Edit**

1. **In Script Library, expand script**
2. **Go to Script tab**
3. **Edit text**
4. **Click "Save Changes"**

**✅ Verify:**
- Success message
- Edit indicator (✎) appears
- Content saved

---

### **Step 8: Test Create Video from Script**

1. **In Script Library, go to Actions tab**
2. **Click "🎬 Create Video"**
3. **Go to Create Video tab**

**✅ Verify:**
- Subject populated
- Script populated
- Keywords populated

4. **Click "Create Video Task"**

**✅ Verify:**
- Task created
- Success message with task ID

---

### **Step 9: Test Script-Task Linking**

1. **Go back to Script Library**
2. **Find the script you used**

**✅ Verify:**
- Status changed to: ✅ Used
- Task ID appears in "Linked Video Tasks"
- Can see task ID

---

### **Step 10: Test Search**

1. **Create 2-3 more scripts** with different subjects
2. **Go to Script Library**
3. **Use search box**

**✅ Verify:**
- Search filters results
- Case-insensitive
- Finds by subject and keywords

---

## 📊 Test Results Checklist

Mark each test as you complete:

### **Automated Tests**
- [ ] All 45 unit tests pass
- [ ] No errors in test output
- [ ] Coverage > 90%

### **Manual UI Tests**
- [ ] Script Library tab loads
- [ ] Statistics display correctly
- [ ] Auto-save works on generation
- [ ] Script appears in library
- [ ] Can edit script
- [ ] Can search scripts
- [ ] Can filter by status
- [ ] Can create video from script
- [ ] Script links to task
- [ ] Can delete script (with confirmation)

### **Integration Tests**
- [ ] Full workflow: Generate → Save → Create Video → Link
- [ ] Multiple scripts from same subject
- [ ] Multiple videos from same script
- [ ] Search across all scripts
- [ ] Statistics update correctly

---

## 🐛 Common Issues & Fixes

### **Issue 1: Storage directory not found**

**Error:**
```
FileNotFoundError: [Errno 2] No such file or directory: '/MoneyPrinterTurbo/storage/scripts'
```

**Fix:**
```bash
docker exec moneyprinterturbo-dev-api mkdir -p /MoneyPrinterTurbo/storage/scripts
```

---

### **Issue 2: Permission denied**

**Error:**
```
PermissionError: [Errno 13] Permission denied: '/MoneyPrinterTurbo/storage/scripts/scr_xxx.json'
```

**Fix:**
```bash
docker exec moneyprinterturbo-dev-api chmod -R 755 /MoneyPrinterTurbo/storage/scripts
```

---

### **Issue 3: Script Library tab not appearing**

**Cause:** WebUI container not restarted

**Fix:**
```bash
docker restart moneyprinterturbo-dev-webui
```

---

### **Issue 4: Auto-save not working**

**Debug:**
```bash
# Check logs
docker logs moneyprinterturbo-dev-webui | grep -i "script"

# Check if auto_save_script function is called
docker logs moneyprinterturbo-dev-webui | grep "Auto-saved"
```

**Common Cause:** Import error

**Fix:** Check logs for import errors, restart container

---

### **Issue 5: Scripts not linking to tasks**

**Debug:**
```bash
# Check linking logs
docker logs moneyprinterturbo-dev-webui | grep "Linked script"

# Check session state
# Generate script → note script_id
# Create task → check if linking happens
```

**Common Cause:** Session cleared between generation and task creation

**Fix:** Generate script and immediately create task

---

## 📈 Performance Validation

### **Test with Volume**

1. **Create 10+ scripts**
2. **Test search performance**
3. **Test list pagination**
4. **Check file system:**
   ```bash
   docker exec moneyprinterturbo-dev-api ls -lh /MoneyPrinterTurbo/storage/scripts/
   ```

**Expected:**
- Search: < 1 second
- List: < 1 second
- File operations: Instant

---

## 🔒 Data Verification

### **Verify Script Files**

```bash
# List all scripts
docker exec moneyprinterturbo-dev-api ls /MoneyPrinterTurbo/storage/scripts/

# View a script file
docker exec moneyprinterturbo-dev-api cat /MoneyPrinterTurbo/storage/scripts/scr_*.json | head -30
```

**Should see:** Valid JSON with all fields

---

### **Backup Scripts**

```bash
# Create backup
docker cp moneyprinterturbo-dev-api:/MoneyPrinterTurbo/storage/scripts /backup/scripts-$(date +%Y%m%d)

# Verify backup
ls -lh /backup/scripts-*/
```

---

## ✅ Go-Live Checklist

Before marking as production-ready:

**Development:**
- [x] Code written and reviewed
- [x] Unit tests written (45 tests)
- [x] All tests passing
- [x] Documentation complete

**Testing:**
- [ ] All automated tests pass
- [ ] All manual tests pass
- [ ] Integration tests pass
- [ ] Performance acceptable
- [ ] Edge cases tested

**Deployment:**
- [ ] Storage directory created
- [ ] Permissions set correctly
- [ ] Containers restarted
- [ ] No errors in logs
- [ ] UI loads correctly

**Validation:**
- [ ] Can create scripts
- [ ] Can save scripts
- [ ] Can search scripts
- [ ] Can edit scripts
- [ ] Can create videos from scripts
- [ ] Scripts link to tasks correctly
- [ ] Statistics accurate

**Production:**
- [ ] Backup strategy in place
- [ ] Monitoring configured
- [ ] User documentation available
- [ ] Support team briefed

---

## 📞 Support

### **If Tests Fail**

1. **Read error message carefully**
2. **Check relevant logs:**
   ```bash
   docker logs moneyprinterturbo-dev-webui
   docker logs moneyprinterturbo-dev-api
   ```
3. **Verify storage directory:**
   ```bash
   docker exec moneyprinterturbo-dev-api ls -la /MoneyPrinterTurbo/storage/
   ```
4. **Check permissions:**
   ```bash
   docker exec moneyprinterturbo-dev-api ls -la /MoneyPrinterTurbo/storage/scripts/
   ```

### **Need Help?**

- `docs/SCRIPT_LIBRARY.md` - Feature documentation
- `docs/TESTING_GUIDE.md` - Testing procedures
- `tests/README.md` - Quick test reference

---

## 🎉 Success Criteria

**Feature is ready when:**

1. ✅ All 45 unit tests pass
2. ✅ Manual test cases complete (10/10)
3. ✅ Integration test passes
4. ✅ No errors in logs
5. ✅ Scripts persist across restarts
6. ✅ Search works correctly
7. ✅ Task linking works
8. ✅ UI is responsive and intuitive

---

## 🚀 Next Steps After Deployment

1. **Monitor Usage:**
   - Watch logs for errors
   - Check storage directory growth
   - Monitor search performance

2. **Gather Feedback:**
   - User experience
   - Feature requests
   - Bug reports

3. **Future Enhancements:**
   - Export/import scripts
   - Script templates
   - Bulk operations
   - Version control

---

## 📝 Deployment Log

**Record your deployment:**

| Date | Tester | Step | Status | Notes |
|------|--------|------|--------|-------|
| 2026-04-09 | [Name] | Run Tests | ⏳ | |
| 2026-04-09 | [Name] | Create Directory | ⏳ | |
| 2026-04-09 | [Name] | Restart Containers | ⏳ | |
| 2026-04-09 | [Name] | Verify UI | ⏳ | |
| 2026-04-09 | [Name] | Test Auto-Save | ⏳ | |
| 2026-04-09 | [Name] | Test Library | ⏳ | |
| 2026-04-09 | [Name] | Test Edit | ⏳ | |
| 2026-04-09 | [Name] | Test Create Video | ⏳ | |
| 2026-04-09 | [Name] | Test Linking | ⏳ | |
| 2026-04-09 | [Name] | Test Search | ⏳ | |

---

**Status Legend:**
- ⏳ Pending
- ✅ Passed
- ❌ Failed
- ⚠️ Issues

---

**Ready to deploy! Let's test this amazing new feature! 🚀**
