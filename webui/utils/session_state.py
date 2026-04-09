"""
Session State Management
Centralized session state with type safety and default values
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any
import streamlit as st

from webui.utils.constants import Defaults, SessionKeys


@dataclass
class AppState:
    """
    Application session state
    All UI state managed in a single dataclass for type safety
    """
    # Video content
    video_subject: str = ""
    video_script: str = ""
    video_terms: str = ""
    video_language: str = ""
    
    # UI state
    ui_language: str = ""
    selected_clip_urls: List[str] = field(default_factory=list)
    preview_items: List[Dict[str, Any]] = field(default_factory=list)
    review_items: List[Dict[str, Any]] = field(default_factory=list)
    
    # Task state
    current_task_id: str = ""
    task_list_page: int = 1
    
    # Bulk operations
    bulk_topics: str = ""
    bulk_created: List[Dict[str, Any]] = field(default_factory=list)
    bulk_failed: List[Dict[str, Any]] = field(default_factory=list)
    
    # Config state
    config_dirty: bool = False
    config_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Cache for API responses
    cache: Dict[str, Any] = field(default_factory=dict)
    
    # Rate limiting
    last_api_calls: List[float] = field(default_factory=list)


def init_session_state() -> AppState:
    """
    Initialize session state with defaults
    
    Returns:
        AppState: The application state object
    """
    if SessionKeys.APP_STATE not in st.session_state:
        st.session_state[SessionKeys.APP_STATE] = AppState()
    
    return st.session_state[SessionKeys.APP_STATE]


def get_state() -> AppState:
    """
    Get current application state
    
    Returns:
        AppState: The application state object
    """
    return st.session_state.get(SessionKeys.APP_STATE, AppState())


def reset_state():
    """Reset application state to defaults"""
    st.session_state[SessionKeys.APP_STATE] = AppState()


def update_state(**kwargs):
    """
    Update application state with provided values
    
    Args:
        **kwargs: Key-value pairs to update in state
    """
    state = get_state()
    for key, value in kwargs.items():
        if hasattr(state, key):
            setattr(state, key, value)


def save_to_cache(key: str, value: Any, ttl: int = 3600):
    """
    Save value to cache with optional TTL
    
    Args:
        key: Cache key
        value: Value to cache
        ttl: Time to live in seconds (default: 1 hour)
    """
    import time
    state = get_state()
    state.cache[key] = {
        "value": value,
        "timestamp": time.time(),
        "ttl": ttl
    }


def get_from_cache(key: str) -> Any:
    """
    Get value from cache if not expired
    
    Args:
        key: Cache key
        
    Returns:
        Cached value or None if not found or expired
    """
    import time
    state = get_state()
    
    if key not in state.cache:
        return None
    
    cached = state.cache[key]
    age = time.time() - cached["timestamp"]
    
    if age > cached["ttl"]:
        # Expired, remove from cache
        del state.cache[key]
        return None
    
    return cached["value"]


def clear_cache():
    """Clear all cached values"""
    state = get_state()
    state.cache.clear()


# Legacy compatibility functions for existing code
def init_legacy_session_state():
    """
    Initialize session state with individual keys (legacy compatibility)
    Gradually migrate to use AppState instead
    """
    defaults = {
        SessionKeys.VIDEO_SUBJECT: "",
        SessionKeys.VIDEO_SCRIPT: "",
        SessionKeys.VIDEO_TERMS: "",
        SessionKeys.VIDEO_LANGUAGE: "",
        SessionKeys.UI_LANGUAGE: "",
        SessionKeys.SELECTED_CLIP_URLS: [],
        SessionKeys.PREVIEW_ITEMS: [],
        SessionKeys.REVIEW_ITEMS: [],
        SessionKeys.CURRENT_TASK_ID: "",
        SessionKeys.TASK_LIST_PAGE: 1,
        SessionKeys.BULK_TOPICS: "",
        SessionKeys.BULK_CREATED: [],
        SessionKeys.BULK_FAILED: [],
        SessionKeys.CONFIG_DIRTY: False,
        SessionKeys.CONFIG_HISTORY: [],
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value
