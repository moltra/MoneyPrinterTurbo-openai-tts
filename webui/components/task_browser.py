"""
Task Browser Component
Provides UI for viewing, searching, and managing video generation tasks
"""
import streamlit as st
import requests
from datetime import datetime
from typing import Optional, Dict, Any, List
from loguru import logger

from webui.i18n import tr


def render_task_browser(api_base_url: str, api_headers: dict):
    """
    Render the task browser interface with search, filtering, and detailed views
    
    Args:
        api_base_url: Base URL for API
        api_headers: API headers including auth
    """
    
    # Search and filter controls
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_query = st.text_input(
            tr("Search tasks"),
            placeholder=tr("Search by task ID or subject..."),
            key="task_search"
        )
    
    with col2:
        page_size = st.selectbox(
            tr("Items per page"),
            options=[10, 25, 50, 100],
            index=0,
            key="task_page_size"
        )
    
    with col3:
        auto_refresh = st.checkbox(
            tr("Auto-refresh"),
            value=False,
            help=tr("Automatically refresh task list every 5 seconds")
        )
    
    st.divider()
    
    # Fetch tasks from API
    try:
        # Initialize page number in session state
        if "task_browser_page" not in st.session_state:
            st.session_state.task_browser_page = 1
        
        page = st.session_state.task_browser_page
        
        # Call API to get tasks
        response = requests.get(
            f"{api_base_url}/api/v1/tasks",
            headers=api_headers,
            params={"page": page, "page_size": page_size},
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        
        if result.get("status") == 200:
            data = result.get("data", {})
            tasks = data.get("tasks", [])
            total = data.get("total", 0)
            
            # Filter tasks by search query if provided
            if search_query:
                tasks = [
                    task for task in tasks
                    if search_query.lower() in task.get("task_id", "").lower()
                    or search_query.lower() in str(task.get("params", {}).get("video_subject", "")).lower()
                ]
            
            # Display task count
            if search_query:
                st.caption(f"{len(tasks)} {tr('tasks found')} ({total} {tr('total')})")
            else:
                st.caption(f"{total} {tr('total tasks')}")
            
            if not tasks:
                st.info(tr("No tasks found"))
            else:
                # Render tasks
                for task in tasks:
                    render_task_card(task, api_base_url, api_headers)
                
                # Pagination
                if total > page_size:
                    st.divider()
                    render_pagination(total, page, page_size)
        
        else:
            st.error(f"{tr('Failed to fetch tasks')}: {result.get('message', 'Unknown error')}")
    
    except requests.exceptions.RequestException as e:
        st.error(f"{tr('Error connecting to API')}: {str(e)}")
        logger.error(f"Task browser API error: {e}")
    
    # Auto-refresh functionality
    if auto_refresh:
        import time
        time.sleep(5)
        st.rerun()


def render_task_card(task: Dict[str, Any], api_base_url: str, api_headers: dict):
    """
    Render a single task card with summary information
    
    Args:
        task: Task data dictionary
        api_base_url: Base URL for API
        api_headers: API headers
    """
    task_id = task.get("task_id", "Unknown")
    state = task.get("state", 0)
    progress = task.get("progress", 0)
    params = task.get("params", {})
    
    # State mapping
    state_map = {
        0: ("⏳", tr("Pending"), "blue"),
        1: ("⚙️", tr("Processing"), "orange"),
        2: ("✅", tr("Completed"), "green"),
        3: ("❌", tr("Failed"), "red")
    }
    
    icon, state_text, color = state_map.get(state, ("❓", tr("Unknown"), "gray"))
    
    # Create expandable card
    with st.expander(
        f"{icon} **{task_id[:8]}...** | {state_text} | {params.get('video_subject', 'N/A')[:50]}",
        expanded=False
    ):
        # Task metadata
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(tr("Status"), state_text)
        
        with col2:
            st.metric(tr("Progress"), f"{progress}%")
        
        with col3:
            st.metric(tr("Subject"), params.get("video_subject", "N/A")[:20])
        
        st.divider()
        
        # Task details tabs
        detail_tabs = st.tabs([
            tr("Details"),
            tr("Parameters"),
            tr("Logs"),
            tr("Actions")
        ])
        
        with detail_tabs[0]:
            render_task_details(task_id, task, api_base_url, api_headers)
        
        with detail_tabs[1]:
            render_task_parameters(params)
        
        with detail_tabs[2]:
            render_task_logs(task_id, api_base_url, api_headers)
        
        with detail_tabs[3]:
            render_task_actions(task_id, task, api_base_url, api_headers)


def render_task_details(task_id: str, task: Dict[str, Any], api_base_url: str, api_headers: dict):
    """Render detailed task information"""
    
    st.write(f"**{tr('Task ID')}:** `{task_id}`")
    
    # Get full task details from API
    try:
        response = requests.get(
            f"{api_base_url}/api/v1/tasks/{task_id}",
            headers=api_headers,
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        
        if result.get("status") == 200:
            full_task = result.get("data", {}).get("task", task)
            
            # Script
            if "video_script" in full_task.get("params", {}):
                st.write(f"**{tr('Script')}:**")
                st.text_area(
                    tr("Generated Script"),
                    value=full_task["params"]["video_script"],
                    height=150,
                    disabled=True,
                    key=f"script_{task_id}"
                )
            
            # Keywords
            if "video_terms" in full_task.get("params", {}):
                st.write(f"**{tr('Keywords')}:**")
                terms = full_task["params"]["video_terms"]
                if isinstance(terms, list):
                    st.write(", ".join(terms))
                else:
                    st.write(terms)
            
            # Video files
            if "combined_videos" in full_task:
                st.write(f"**{tr('Generated Videos')}:**")
                for idx, video_url in enumerate(full_task["combined_videos"], 1):
                    st.write(f"{idx}. {video_url}")
                    if st.button(tr("Download"), key=f"download_{task_id}_{idx}"):
                        st.info(tr("Video download link") + f": {video_url}")
        
        else:
            st.warning(tr("Could not fetch full task details"))
    
    except Exception as e:
        logger.error(f"Error fetching task details: {e}")
        st.error(f"{tr('Error')}: {str(e)}")


def render_task_parameters(params: Dict[str, Any]):
    """Render task parameters in a clean format"""
    
    # Core parameters
    st.write(f"**{tr('Video Settings')}:**")
    
    param_display = {
        "video_aspect": tr("Aspect Ratio"),
        "video_concat_mode": tr("Concat Mode"),
        "video_clip_duration": tr("Clip Duration"),
        "video_count": tr("Video Count"),
        "video_language": tr("Language"),
        "video_source": tr("Video Source"),
    }
    
    for key, label in param_display.items():
        if key in params:
            st.write(f"- **{label}:** {params[key]}")
    
    # Voice settings
    if any(k.startswith("voice_") for k in params.keys()):
        st.write(f"\n**{tr('Voice Settings')}:**")
        voice_params = {
            "voice_name": tr("Voice"),
            "voice_rate": tr("Rate"),
            "voice_volume": tr("Volume"),
            "voice_pitch": tr("Pitch"),
        }
        for key, label in voice_params.items():
            if key in params:
                st.write(f"- **{label}:** {params[key]}")
    
    # Show all params in JSON
    with st.expander(tr("View Raw Parameters")):
        st.json(params)


def render_task_logs(task_id: str, api_base_url: str, api_headers: dict):
    """
    Render task-specific logs
    
    Note: This requires an API endpoint to fetch logs by task_id
    For now, shows instructions for manual log viewing
    """
    
    st.write(f"**{tr('Task Logs')}:** `{task_id}`")
    
    # Command to view logs
    st.code(f"docker logs moneyprinterturbo-dev-api | grep '[Task: {task_id[:8]}]'", language="bash")
    
    st.caption(tr("Log streaming from API coming soon"))
    
    # Placeholder for future log streaming
    st.info(
        tr("To view logs for this task, run the command above in your terminal.\n\n"
           "Future enhancement: Real-time log streaming will be available here.")
    )


def render_task_actions(task_id: str, task: Dict[str, Any], api_base_url: str, api_headers: dict):
    """Render task action buttons"""
    
    state = task.get("state", 0)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Refresh button
        if st.button(tr("Refresh"), key=f"refresh_{task_id}", use_container_width=True):
            st.rerun()
    
    with col2:
        # Delete button (only for completed/failed tasks)
        if state in [2, 3]:  # Completed or Failed
            if st.button(tr("Delete"), key=f"delete_{task_id}", type="secondary", use_container_width=True):
                if delete_task(task_id, api_base_url, api_headers):
                    st.success(tr("Task deleted"))
                    st.rerun()
                else:
                    st.error(tr("Failed to delete task"))
    
    with col3:
        # Retry button (only for failed tasks)
        if state == 3:  # Failed
            if st.button(tr("Retry"), key=f"retry_{task_id}", type="primary", use_container_width=True):
                st.info(tr("Retry functionality coming soon"))


def delete_task(task_id: str, api_base_url: str, api_headers: dict) -> bool:
    """
    Delete a task via API
    
    Args:
        task_id: Task ID to delete
        api_base_url: Base URL for API
        api_headers: API headers
        
    Returns:
        True if deletion successful, False otherwise
    """
    try:
        response = requests.delete(
            f"{api_base_url}/api/v1/tasks/{task_id}",
            headers=api_headers,
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        return result.get("status") == 200
    
    except Exception as e:
        logger.error(f"Error deleting task {task_id}: {e}")
        return False


def render_pagination(total: int, current_page: int, page_size: int):
    """
    Render pagination controls
    
    Args:
        total: Total number of items
        current_page: Current page number (1-indexed)
        page_size: Items per page
    """
    total_pages = (total + page_size - 1) // page_size
    
    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
    
    with col1:
        if st.button("⏮️ " + tr("First"), disabled=(current_page == 1), use_container_width=True):
            st.session_state.task_browser_page = 1
            st.rerun()
    
    with col2:
        if st.button("◀️ " + tr("Previous"), disabled=(current_page == 1), use_container_width=True):
            st.session_state.task_browser_page = current_page - 1
            st.rerun()
    
    with col3:
        st.write(f"<div style='text-align: center; padding-top: 8px;'>{tr('Page')} {current_page} {tr('of')} {total_pages}</div>", unsafe_allow_html=True)
    
    with col4:
        if st.button(tr("Next") + " ▶️", disabled=(current_page == total_pages), use_container_width=True):
            st.session_state.task_browser_page = current_page + 1
            st.rerun()
    
    with col5:
        if st.button(tr("Last") + " ⏭️", disabled=(current_page == total_pages), use_container_width=True):
            st.session_state.task_browser_page = total_pages
            st.rerun()
