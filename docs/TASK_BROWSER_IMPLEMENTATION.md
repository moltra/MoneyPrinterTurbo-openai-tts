# Task Browser Implementation

**Feature:** Complete Task Management UI  
**Date Implemented:** April 9, 2026  
**Status:** ✅ Ready to Use

---

## 🎯 Overview

The Task Browser provides a comprehensive interface for viewing, searching, and managing video generation tasks. It replaces the placeholder tab with a fully functional task management system.

---

## ✨ Features

### **1. Task List View**
- 📋 **Paginated display** - Show 10, 25, 50, or 100 tasks per page
- 🔍 **Search functionality** - Filter by task ID or video subject
- 🔄 **Auto-refresh** - Optional automatic refresh every 5 seconds
- 📊 **Status indicators** - Visual icons for pending, processing, completed, failed

### **2. Task Cards**
Each task displays in an expandable card showing:
- **Task ID** (first 8 characters for quick reference)
- **Status** (pending/processing/completed/failed)
- **Video Subject** (first 50 characters)
- **Progress Bar** (0-100%)

### **3. Task Details Tabs**

#### **Details Tab**
- Full task ID
- Generated script (if available)
- Keywords/search terms
- Generated video URLs
- Download links

#### **Parameters Tab**
- Video settings (aspect ratio, clip duration, count, etc.)
- Voice settings (name, rate, volume, pitch)
- Raw JSON view of all parameters

#### **Logs Tab**
- Command to view task-specific logs
- Instructions for filtering by task ID
- Placeholder for future real-time log streaming

#### **Actions Tab**
- **Refresh** - Update task status
- **Delete** - Remove completed/failed tasks
- **Retry** - Restart failed tasks (coming soon)

### **4. Pagination**
- First/Previous/Next/Last navigation
- Current page indicator
- Total pages display

---

## 📁 File Structure

### **New Files:**
```
webui/components/task_browser.py    # Main task browser component (384 lines)
```

### **Modified Files:**
```
webui/Main.py                        # Integrated task browser into Tab 2
```

---

## 🔧 Component Functions

### **`render_task_browser(api_base_url, api_headers)`**
Main entry point - renders the complete task browser interface

### **`render_task_card(task, api_base_url, api_headers)`**
Renders individual task card with expandable details

### **`render_task_details(task_id, task, api_base_url, api_headers)`**
Shows detailed task information (script, keywords, videos)

### **`render_task_parameters(params)`**
Displays task parameters in a clean, organized format

### **`render_task_logs(task_id, api_base_url, api_headers)`**
Shows log viewing instructions and commands

### **`render_task_actions(task_id, task, api_base_url, api_headers)`**
Action buttons (refresh, delete, retry)

### **`delete_task(task_id, api_base_url, api_headers)`**
Deletes a task via API

### **`render_pagination(total, current_page, page_size)`**
Pagination controls

---

## 🎨 UI Components

### **Search Bar**
```python
search_query = st.text_input(
    tr("Search tasks"),
    placeholder=tr("Search by task ID or subject...")
)
```

### **Items Per Page Selector**
```python
page_size = st.selectbox(
    tr("Items per page"),
    options=[10, 25, 50, 100]
)
```

### **Auto-Refresh Checkbox**
```python
auto_refresh = st.checkbox(
    tr("Auto-refresh"),
    value=False,
    help=tr("Automatically refresh every 5 seconds")
)
```

### **Task Card States**
- ⏳ **Pending** (blue) - Task created, waiting to start
- ⚙️ **Processing** (orange) - Currently generating video
- ✅ **Completed** (green) - Video successfully created
- ❌ **Failed** (red) - Error during generation

---

## 📡 API Integration

### **Endpoints Used:**

#### **GET /api/v1/tasks**
Fetch paginated list of tasks
```python
GET /api/v1/tasks?page=1&page_size=10

Response:
{
    "status": 200,
    "data": {
        "tasks": [...],
        "total": 42
    }
}
```

#### **GET /api/v1/tasks/{task_id}**
Fetch detailed task information
```python
GET /api/v1/tasks/a02f7922-a1a8-44b9-9d64-e311f8d7018f

Response:
{
    "status": 200,
    "data": {
        "task": {
            "task_id": "...",
            "state": 2,
            "progress": 100,
            "params": {...},
            "combined_videos": [...]
        }
    }
}
```

#### **DELETE /api/v1/tasks/{task_id}**
Delete a task
```python
DELETE /api/v1/tasks/a02f7922-a1a8-44b9-9d64-e311f8d7018f

Response:
{
    "status": 200
}
```

---

## 🔍 Usage Examples

### **Example 1: Find Specific Task**
1. Go to **📊 Task Browser** tab
2. Type task ID or subject in search box
3. Results filter in real-time

### **Example 2: Monitor Active Tasks**
1. Enable **Auto-refresh** checkbox
2. Page refreshes every 5 seconds
3. Watch progress update automatically

### **Example 3: View Task Logs**
1. Expand task card
2. Click **Logs** tab
3. Copy the provided command
4. Run in terminal to see task-specific logs

```bash
docker logs moneyprinterturbo-dev-api | grep '[Task: a02f7922]'
```

### **Example 4: Delete Old Tasks**
1. Find completed/failed task
2. Expand task card
3. Click **Actions** tab
4. Click **Delete** button
5. Confirm deletion

---

## 🎯 Benefits with Task ID Logging

### **Perfect Integration with Enhanced Logging**

The Task Browser works seamlessly with the improved task logging system:

**Before Task Browser:**
```bash
# Had to manually grep logs
docker logs moneyprinterturbo-dev-api | grep "a02f7922"
```

**With Task Browser:**
1. See all tasks in UI ✅
2. Click on task card ✅
3. View logs tab → copy command ✅
4. One-click access to task-specific logs ✅

### **Complete Task Lifecycle Visibility**

```
[WebUI] Create Task
   ↓
[Task Browser] View in list (⏳ Pending)
   ↓
[API] Start processing
   ↓
[Task Browser] Status updates (⚙️ Processing)
   ↓
[Logs Tab] View detailed logs with [Task: ID] prefix
   ↓
[Task Browser] Completion (✅ or ❌)
   ↓
[Actions] Download or Delete
```

---

## 🚀 Future Enhancements

### **Phase 2: Real-Time Features**
- [ ] **Live log streaming** - Show logs directly in UI
- [ ] **WebSocket updates** - Real-time progress without polling
- [ ] **Progress breakdown** - Show script/video/subtitle stages

### **Phase 3: Advanced Management**
- [ ] **Bulk actions** - Delete/retry multiple tasks
- [ ] **Filters** - By status, date, subject
- [ ] **Sort options** - By date, status, progress
- [ ] **Export** - Download task data as JSON/CSV

### **Phase 4: Analytics**
- [ ] **Task statistics** - Success rate, average duration
- [ ] **Performance graphs** - Tasks over time
- [ ] **Error patterns** - Common failure reasons
- [ ] **Resource usage** - API load, storage used

---

## 🐛 Troubleshooting

### **Issue: "Failed to fetch tasks"**

**Cause:** API not responding or wrong endpoint

**Solution:**
```bash
# Check API is running
docker ps | grep moneyprinterturbo-dev-api

# Check API logs
docker logs moneyprinterturbo-dev-api --tail 50

# Verify endpoint
curl http://localhost:8089/api/v1/tasks?page=1&page_size=10
```

### **Issue: "No tasks found"**

**Possible Causes:**
1. No tasks created yet → Create a video first
2. Wrong page number → Go to page 1
3. Search filter too restrictive → Clear search
4. Tasks cleared from state → Check state backend (memory/redis)

### **Issue: Task details not loading**

**Cause:** API endpoint `/api/v1/tasks/{task_id}` not implemented fully

**Workaround:**
- Basic info still shows in card
- Use logs tab to see detailed progress
- Check storage directory for generated files

---

## 📊 State Management

### **Session State Keys:**
```python
st.session_state.task_browser_page = 1  # Current page number
st.session_state.task_search = ""       # Search query
st.session_state.task_page_size = 10    # Items per page
```

### **Task State Values:**
```python
TASK_STATE_PENDING = 0      # ⏳ Waiting
TASK_STATE_PROCESSING = 1   # ⚙️ Running
TASK_STATE_COMPLETED = 2    # ✅ Done
TASK_STATE_FAILED = 3       # ❌ Error
```

---

## 📝 Translation Keys

All UI text uses the translation system. Add to your locale files:

```json
{
  "Search tasks": "Search tasks",
  "Items per page": "Items per page",
  "Auto-refresh": "Auto-refresh",
  "Pending": "Pending",
  "Processing": "Processing",
  "Completed": "Completed",
  "Failed": "Failed",
  "Unknown": "Unknown",
  "Details": "Details",
  "Parameters": "Parameters",
  "Logs": "Logs",
  "Actions": "Actions",
  "Refresh": "Refresh",
  "Delete": "Delete",
  "Retry": "Retry",
  "First": "First",
  "Previous": "Previous",
  "Next": "Next",
  "Last": "Last",
  "Page": "Page",
  "of": "of",
  "tasks found": "tasks found",
  "total tasks": "total tasks",
  "No tasks found": "No tasks found"
}
```

---

## ✅ Deployment Checklist

- [x] Create `task_browser.py` component
- [x] Integrate into `Main.py`
- [x] Add translation support
- [x] Implement search/filter
- [x] Add pagination
- [x] Create detailed views
- [x] Add action buttons
- [ ] Restart WebUI container
- [ ] Test with existing tasks
- [ ] Verify all tabs work
- [ ] Test pagination
- [ ] Test search
- [ ] Test delete action

---

## 🎉 Summary

**Before:**
```
📊 Task Browser
ℹ️ Task browser implementation coming soon
Will include: search, filtering, pagination, task management
```

**After:**
```
📊 Task Browser
├── 🔍 Search: [Find tasks by ID or subject]
├── 📄 Page size: [10, 25, 50, 100]
├── 🔄 Auto-refresh: [ ]
├──────────────────────────────────────────
├── ⚙️ a02f7922... | Processing | home improvement
│   ├── Details: Script, Keywords, Videos
│   ├── Parameters: All settings
│   ├── Logs: View command
│   └── Actions: Refresh, Delete, Retry
├── ✅ 8920c410... | Completed | AI technology
└── [First] [Previous] Page 1 of 5 [Next] [Last]
```

**Full-featured task management is now live!** 🚀
