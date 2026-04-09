"""
MoneyPrinterTurbo WebUI - Refactored with Secure Components
This is a refactored version of Main.py with:
- Secure API key handling
- Input validation
- Better error handling
- Progress feedback
- Modular components

To use: Rename Main.py to Main_original.py and rename this file to Main.py
"""
import os
import platform
import pathlib
import json
import re
import shutil
import signal
import sys
import time
from uuid import uuid4

import requests
import streamlit as st
from loguru import logger

# Add root directory to path
root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from app.config import config
from app.models.schema import (
    VideoAspect,
    VideoConcatMode,
    VideoParams,
    VideoTransitionMode,
)
from app.services import llm, voice
from app.utils import utils

# Import new WebUI components
from webui.components.llm_config import render_llm_config
from webui.components.video_source_config import (
    render_video_source_config,
    render_video_api_key_management
)
from webui.components.voice_config import (
    render_openai_tts_config,
    render_siliconflow_config
)
from webui.components.task_creation import (
    create_video_task_with_validation,
    create_bulk_tasks_with_progress,
    validate_and_show_params_summary
)
from webui.utils.constants import ConfigKeys, Defaults, SessionKeys
from webui.utils.session_state import init_legacy_session_state
from webui.utils.validation import validate_file_path

st.set_page_config(
    page_title="MoneyPrinterTurbo",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={
        "Report a bug": "https://github.com/harry0703/MoneyPrinterTurbo/issues",
        "About": "# MoneyPrinterTurbo\nSimply provide a topic or keyword for a video, and it will "
        "automatically generate the video copy, video materials, video subtitles, "
        "and video background music before synthesizing a high-definition short "
        "video.\n\nhttps://github.com/harry0703/MoneyPrinterTurbo",
    },
)

is_dev_mode = (os.environ.get("MPT_MODE", "") or "").strip().lower() == "dev"

# Styling
streamlit_style = """
<style>
h1 {
    padding-top: 0 !important;
}
</style>
"""
st.markdown(streamlit_style, unsafe_allow_html=True)

if is_dev_mode:
    st.markdown(
        """
<style>
  /* DEV mode tint */
  [data-testid="stAppViewContainer"] {
    background: linear-gradient(180deg, rgba(255, 239, 213, 0.35) 0%, rgba(255, 239, 213, 0.0) 40%);
  }
  [data-testid="stHeader"] {
    background: rgba(255, 239, 213, 0.65);
  }
</style>
""",
        unsafe_allow_html=True,
    )

# Initialize session state
init_legacy_session_state()


def _api_base_url() -> str:
    base_url = (os.environ.get("MPT_API_BASE_URL", "") or "").strip()
    if base_url:
        base_url = base_url.rstrip("/")
        try:
            if os.path.exists("/.dockerenv") and base_url.endswith(":8089"):
                return "http://moneyprinterturbo-dev-api:8080"
        except Exception:
            pass
        return base_url
    return "http://127.0.0.1:8080"


def _public_api_base_url() -> str:
    base_url = (os.environ.get("MPT_PUBLIC_API_BASE_URL", "") or "").strip()
    if base_url:
        return base_url.rstrip("/")
    return _api_base_url()


def _safe_task_dir(task_id: str) -> pathlib.Path:
    """Get task directory with path traversal protection"""
    base_dir = pathlib.Path(utils.task_dir()).resolve()
    candidate = (base_dir / (task_id or "")).resolve()
    
    # Validate path
    is_valid, error = validate_file_path(task_id, str(base_dir))
    if not is_valid:
        raise ValueError(f"Invalid task_id: {error}")
    
    try:
        candidate.relative_to(base_dir)
        return candidate
    except ValueError:
        raise ValueError(f"Invalid task_id: path traversal detected")


def _api_key() -> str:
    return (os.environ.get("MPT_API_KEY", "") or config.app.get("api_key", "") or "").strip()


def _api_headers() -> dict:
    api_key = _api_key()
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["x-api-key"] = api_key
    return headers


# Import translation helper
def tr(key):
    """Translation helper - uses existing i18n system"""
    from webui.i18n import tr as i18n_tr
    return i18n_tr(key)


# ============================================================================
# MAIN UI
# ============================================================================

def main():
    st.markdown(
        f'<h1 style="margin-top: 0;">{"💻 " if is_dev_mode else ""}MoneyPrinterTurbo</h1>',
        unsafe_allow_html=True,
    )
    
    # ========================================================================
    # SIDEBAR - Configuration
    # ========================================================================
    with st.sidebar:
        st.title(tr("Configuration"))
        
        # Language selection
        selected_language = st.selectbox(
            tr("Language"),
            options=["zh-CN", "en-US", "zh-TW"],
            index=0 if config.ui.get("language") == "zh" else 1,
        )
        
        language_map = {
            "zh-CN": "zh",
            "en-US": "en",
            "zh-TW": "zh-TW"
        }
        config.ui["language"] = language_map.get(selected_language, "zh")
        
        st.divider()
        
        # Configuration Panels
        tabs = st.tabs([
            tr("LLM"),
            tr("Video Source"),
            tr("Advanced")
        ])
        
        with tabs[0]:
            # Use new secure LLM config component
            render_llm_config()
        
        with tabs[1]:
            # Use new secure video source config component
            render_video_source_config()
        
        with tabs[2]:
            # Advanced settings (keep existing implementation for now)
            st.write(tr("Advanced Settings"))
            st.caption(tr("These settings are for advanced users"))
            
            # API Key for webui access
            webui_api_key = config.app.get("api_key", "")
            from webui.utils.security import render_secure_api_key_input
            was_updated, new_key = render_secure_api_key_input(
                label=tr("WebUI API Key"),
                config_key="api_key",
                help_text=tr("Optional API key for WebUI authentication")
            )
            if was_updated:
                if new_key:
                    config.app["api_key"] = new_key
                else:
                    config.app.pop("api_key", None)
                config.save_config()
        
        st.divider()
        
        # Save config button
        if st.button(tr("Save Configuration"), type="primary", use_container_width=True):
            config.save_config()
            st.success(tr("Configuration saved successfully"))
    
    # ========================================================================
    # MAIN CONTENT - Task Creation
    # ========================================================================
    
    main_tabs = st.tabs([
        tr("Create Video"),
        tr("Bulk Create"),
        tr("Task Browser"),
        tr("API Key Management")
    ])
    
    # Tab 1: Single Video Creation
    with main_tabs[0]:
        st.subheader(tr("Create Single Video"))
        
        # Get default params from config
        params = VideoParams(
            video_subject="",
            video_script="",
            video_terms="",
            video_aspect=config.ui.get(ConfigKeys.VIDEO_ASPECT, Defaults.VIDEO_ASPECT),
            video_concat_mode=config.ui.get(ConfigKeys.VIDEO_CONCAT_MODE, Defaults.VIDEO_CONCAT_MODE),
            video_clip_duration=config.ui.get(ConfigKeys.VIDEO_CLIP_DURATION, Defaults.CLIP_DURATION),
            video_count=config.ui.get(ConfigKeys.VIDEO_COUNT, Defaults.VIDEO_COUNT),
            video_source=config.app.get(ConfigKeys.VIDEO_SOURCE, Defaults.VIDEO_SOURCE),
            video_transition=config.ui.get(ConfigKeys.VIDEO_TRANSITION, Defaults.VIDEO_TRANSITION),
            voice_name=config.ui.get(ConfigKeys.VOICE_NAME, Defaults.VOICE_NAME),
            voice_rate=config.ui.get(ConfigKeys.VOICE_RATE, Defaults.VOICE_RATE),
            voice_volume=config.ui.get(ConfigKeys.VOICE_VOLUME, Defaults.VOICE_VOLUME),
            voice_pitch=config.ui.get(ConfigKeys.VOICE_PITCH, Defaults.VOICE_PITCH),
            bgm_type=config.ui.get(ConfigKeys.BGM_TYPE, Defaults.BGM_TYPE),
            bgm_volume=config.ui.get(ConfigKeys.BGM_VOLUME, Defaults.BGM_VOLUME),
            subtitle_enabled=config.ui.get(ConfigKeys.SUBTITLE_ENABLED, Defaults.SUBTITLE_ENABLED),
            n_threads=config.ui.get(ConfigKeys.N_THREADS, Defaults.N_THREADS),
            paragraph_number=config.ui.get(ConfigKeys.PARAGRAPH_NUMBER, Defaults.PARAGRAPH_NUMBER),
        )
        
        # Video subject/script input
        col1, col2 = st.columns(2)
        
        with col1:
            video_subject = st.text_input(
                tr("Video Subject"),
                value=st.session_state.get(SessionKeys.VIDEO_SUBJECT, ""),
                help=tr("Topic or keyword for video generation"),
                placeholder=tr("e.g., AI in healthcare")
            )
            params.video_subject = video_subject.strip()
            st.session_state[SessionKeys.VIDEO_SUBJECT] = video_subject
        
        with col2:
            video_script = st.text_area(
                tr("Video Script"),
                value=st.session_state.get(SessionKeys.VIDEO_SCRIPT, ""),
                help=tr("Provide your own script (optional)"),
                height=100
            )
            params.video_script = video_script.strip()
            st.session_state[SessionKeys.VIDEO_SCRIPT] = video_script
        
        # Quick settings
        st.write(tr("Quick Settings"))
        
        cols = st.columns(4)
        
        with cols[0]:
            params.video_aspect = st.selectbox(
                tr("Aspect Ratio"),
                options=["16:9", "9:16", "1:1"],
                index=0
            )
        
        with cols[1]:
            params.video_source = st.selectbox(
                tr("Video Source"),
                options=["pexels", "pixabay", "local"],
                index=0
            )
        
        with cols[2]:
            params.video_clip_duration = st.number_input(
                tr("Clip Duration (s)"),
                min_value=1,
                max_value=60,
                value=Defaults.CLIP_DURATION
            )
        
        with cols[3]:
            params.video_count = st.number_input(
                tr("Number of Clips"),
                min_value=1,
                max_value=100,
                value=Defaults.VIDEO_COUNT
            )
        
        st.divider()
        
        # Create task button
        if st.button(tr("Create Video Task"), type="primary", use_container_width=True):
            # Use new validation and task creation component
            task_data = create_video_task_with_validation(
                _api_base_url(),
                _api_headers(),
                params
            )
            
            if task_data:
                task_id = task_data.get("task_id", "")
                st.session_state[SessionKeys.CURRENT_TASK_ID] = task_id
                
                # Show task details
                with st.expander(tr("Task Details"), expanded=True):
                    st.json(task_data)
    
    # Tab 2: Bulk Creation
    with main_tabs[1]:
        st.subheader(tr("Bulk Task Creation"))
        st.caption(tr("Create multiple video tasks at once"))
        
        bulk_topics = st.text_area(
            tr("Topics (one per line)"),
            value=st.session_state.get(SessionKeys.BULK_TOPICS, ""),
            height=200,
            placeholder=tr("Enter one topic per line\nExample:\nAI in healthcare\nClimate change solutions\nSpace exploration")
        )
        st.session_state[SessionKeys.BULK_TOPICS] = bulk_topics
        
        if st.button(tr("Create Bulk Tasks"), type="primary"):
            topics = [t.strip() for t in bulk_topics.split("\n") if t.strip()]
            
            if not topics:
                st.warning(tr("Please enter at least one topic"))
            else:
                # Use base params from config
                base_params = VideoParams(
                    video_subject="",  # Will be filled by topic
                    video_aspect=config.ui.get(ConfigKeys.VIDEO_ASPECT, Defaults.VIDEO_ASPECT),
                    video_source=config.app.get(ConfigKeys.VIDEO_SOURCE, Defaults.VIDEO_SOURCE),
                    video_clip_duration=config.ui.get(ConfigKeys.VIDEO_CLIP_DURATION, Defaults.CLIP_DURATION),
                    video_count=config.ui.get(ConfigKeys.VIDEO_COUNT, Defaults.VIDEO_COUNT),
                )
                
                # Create tasks with progress
                successful, failed = create_bulk_tasks_with_progress(
                    _api_base_url(),
                    _api_headers(),
                    base_params,
                    topics
                )
                
                # Store results in session
                st.session_state[SessionKeys.BULK_CREATED] = successful
                st.session_state[SessionKeys.BULK_FAILED] = failed
    
    # Tab 3: Task Browser (placeholder - would need full implementation)
    with main_tabs[2]:
        st.subheader(tr("Task Browser"))
        st.info(tr("Task browser implementation coming soon"))
        st.caption(tr("Will include: search, filtering, pagination, task management"))
    
    # Tab 4: API Key Management
    with main_tabs[3]:
        render_video_api_key_management()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        logger.exception("Unhandled exception in main()")
