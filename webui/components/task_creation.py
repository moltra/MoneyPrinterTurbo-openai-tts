"""
Task Creation Component
Handles video task creation with validation and progress feedback
"""
import streamlit as st
import requests
from typing import Optional, Dict, Any

from app.models.schema import VideoParams
from webui.i18n import tr
from webui.utils.validation import validate_video_params
from webui.utils.api_helpers import safe_api_call, with_progress
from loguru import logger


def create_video_task_with_validation(
    api_base_url: str,
    api_headers: dict,
    params: VideoParams
) -> Optional[Dict[str, Any]]:
    """
    Create video task with comprehensive validation
    
    Args:
        api_base_url: Base URL for API
        api_headers: API headers including auth
        params: Video generation parameters
        
    Returns:
        Task response dict or None if validation failed
    """
    # Validate parameters
    is_valid, errors = validate_video_params(params)
    
    if not is_valid:
        st.error(tr("Validation Failed"))
        for error in errors:
            st.error(f"• {error}")
        return None
    
    # Create task via API
    def _create_task():
        create_url = f"{api_base_url}/api/v1/videos"
        response = requests.post(
            create_url,
            json=params.model_dump(),
            headers=api_headers,
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    
    result = safe_api_call(
        _create_task,
        error_msg=tr("Failed to create video task"),
        spinner_text=tr("Creating task..."),
        show_spinner=True
    )
    
    # API uses "status" field, not "code"
    if result and result.get("status") == 200:
        task_data = result.get("data", {})
        task_id = task_data.get("task_id", "")
        
        if task_id:
            st.success(tr("Task created successfully") + f": {task_id}")
            logger.info(f"Task created: {task_id}")
            return task_data
        else:
            st.error(tr("Task created but no task_id returned"))
            return None
    else:
        error_msg = result.get("message", tr("Unknown error")) if result else tr("No response from server")
        st.error(tr("Failed to create task") + f": {error_msg}")
        return None


def create_bulk_tasks_with_progress(
    api_base_url: str,
    api_headers: dict,
    base_params: VideoParams,
    topics: list[str]
) -> tuple[list[Dict], list[Dict]]:
    """
    Create multiple video tasks with progress feedback
    
    Args:
        api_base_url: Base URL for API
        api_headers: API headers including auth
        base_params: Base parameters to use for all tasks
        topics: List of topics to create tasks for
        
    Returns:
        Tuple of (successful_tasks, failed_tasks)
    """
    from webui.utils.validation import validate_bulk_topics
    
    # Validate topics first
    is_valid, valid_topics, errors = validate_bulk_topics("\n".join(topics))
    
    if not is_valid:
        st.error(tr("Validation Failed"))
        for error in errors:
            st.error(f"• {error}")
        return [], []
    
    if not valid_topics:
        st.warning(tr("No valid topics to process"))
        return [], []
    
    # Process each topic with progress bar
    def process_topic(topic: str) -> Dict[str, Any]:
        # Create params for this topic
        task_params = base_params.model_copy()
        task_params.video_subject = topic
        
        # Create task
        create_url = f"{api_base_url}/api/v1/videos"
        response = requests.post(
            create_url,
            json=task_params.model_dump(),
            headers=api_headers,
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        
        if result.get("code") == 0:
            task_data = result.get("data", {})
            return {
                "topic": topic,
                "task_id": task_data.get("task_id", ""),
                "status": "success"
            }
        else:
            raise Exception(result.get("message", "Unknown error"))
    
    successful, failed = with_progress(
        valid_topics,
        process_topic,
        status_text_template=tr("Processing") + " {current}/{total}: {item}",
        error_handler=None
    )
    
    # Show summary
    if successful:
        st.success(
            tr("Successfully created") + f" {len(successful)} " +
            tr("tasks") + " / " + tr("Total") + f": {len(valid_topics)}"
        )
    
    if failed:
        st.error(
            tr("Failed") + f": {len(failed)} " + tr("tasks")
        )
        with st.expander(tr("View failed tasks")):
            for fail_info in failed:
                st.write(f"• {fail_info['item']}: {fail_info['error']}")
    
    return successful, failed


def validate_and_show_params_summary(params: VideoParams) -> bool:
    """
    Validate parameters and show summary before task creation
    
    Args:
        params: Video generation parameters
        
    Returns:
        True if valid and user confirmed, False otherwise
    """
    # Validate
    is_valid, errors = validate_video_params(params)
    
    if not is_valid:
        st.error(tr("Validation Failed"))
        for error in errors:
            st.error(f"• {error}")
        return False
    
    # Show summary
    with st.expander(tr("Task Parameters Summary"), expanded=False):
        st.write(f"**{tr('Video Subject')}:** {params.video_subject or tr('From script')}")
        st.write(f"**{tr('Video Source')}:** {params.video_source}")
        st.write(f"**{tr('Video Aspect')}:** {params.video_aspect}")
        st.write(f"**{tr('Video Duration')}:** {params.video_clip_duration}s x {params.video_count} clips")
        st.write(f"**{tr('Voice')}:** {params.voice_name}")
        st.write(f"**{tr('BGM')}:** {params.bgm_type} (volume: {params.bgm_volume})")
        st.write(f"**{tr('Subtitles')}:** {tr('Enabled') if params.subtitle_enabled else tr('Disabled')}")
    
    return True
