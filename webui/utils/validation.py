"""
Input Validation Utilities
Validate user inputs before processing
"""
from typing import Tuple, List
from app.config import config
from app.models.schema import VideoParams
from webui.utils.constants import UIMessages, VideoProviders


def validate_video_params(params: VideoParams) -> Tuple[bool, List[str]]:
    """
    Validate video generation parameters
    
    Args:
        params: Video generation parameters
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check subject or script
    if not params.video_subject.strip() and not params.video_script.strip():
        errors.append(UIMessages.ERROR_EMPTY_SCRIPT)
    
    # Check API keys for video providers
    if params.video_source in (VideoProviders.PEXELS, VideoProviders.PIXABAY):
        api_keys = config.app.get(f"{params.video_source}_api_keys", [])
        if not api_keys:
            errors.append(f"{params.video_source.title()} {UIMessages.ERROR_API_KEY_MISSING}")
    
    # Check LLM API key if generating script
    if params.video_subject and not params.video_script:
        llm_provider = config.app.get("llm_provider", "").lower()
        if llm_provider:
            api_key = config.app.get(f"{llm_provider}_api_key", "")
            if not api_key:
                errors.append(f"LLM {UIMessages.ERROR_API_KEY_MISSING}")
    
    # Validate numeric ranges
    if params.video_clip_duration <= 0:
        errors.append("Video clip duration must be greater than 0")
    
    if params.video_count <= 0:
        errors.append("Video count must be greater than 0")
    
    if params.n_threads <= 0:
        errors.append("Number of threads must be greater than 0")
    
    # Validate voice settings
    if params.voice_rate < 0.5 or params.voice_rate > 2.0:
        errors.append("Voice rate must be between 0.5 and 2.0")
    
    if params.voice_volume < 0 or params.voice_volume > 2.0:
        errors.append("Voice volume must be between 0 and 2.0")
    
    if params.bgm_volume < 0 or params.bgm_volume > 1.0:
        errors.append("BGM volume must be between 0 and 1.0")
    
    return len(errors) == 0, errors


def validate_config_change(key: str, value: any) -> Tuple[bool, str]:
    """
    Validate a configuration change before saving
    
    Args:
        key: Configuration key
        value: New value
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # API keys should not be empty strings (either None or actual value)
    if "api_key" in key.lower() and value == "":
        return False, "API key cannot be empty. Leave unset or provide a value."
    
    # Numeric validations
    numeric_ranges = {
        "video_clip_duration": (1, 60),
        "video_count": (1, 100),
        "n_threads": (1, 32),
        "font_size": (10, 200),
        "stroke_width": (0, 10),
        "voice_rate": (0.5, 2.0),
        "voice_volume": (0, 2.0),
        "voice_pitch": (0.5, 2.0),
        "bgm_volume": (0, 1.0),
    }
    
    if key in numeric_ranges:
        min_val, max_val = numeric_ranges[key]
        try:
            num_value = float(value)
            if not (min_val <= num_value <= max_val):
                return False, f"{key} must be between {min_val} and {max_val}"
        except (ValueError, TypeError):
            return False, f"{key} must be a number"
    
    return True, ""


def validate_bulk_topics(topics_text: str) -> Tuple[bool, List[str], List[str]]:
    """
    Validate bulk topic list
    
    Args:
        topics_text: Multi-line text with one topic per line
        
    Returns:
        Tuple of (is_valid, valid_topics, errors)
    """
    errors = []
    valid_topics = []
    
    if not topics_text.strip():
        errors.append("Topic list is empty")
        return False, [], errors
    
    lines = topics_text.strip().split("\n")
    for i, line in enumerate(lines, 1):
        topic = line.strip()
        if not topic:
            continue
        
        if len(topic) < 3:
            errors.append(f"Line {i}: Topic too short (minimum 3 characters)")
            continue
        
        if len(topic) > 200:
            errors.append(f"Line {i}: Topic too long (maximum 200 characters)")
            continue
        
        valid_topics.append(topic)
    
    if not valid_topics:
        errors.append("No valid topics found")
        return False, [], errors
    
    if len(valid_topics) > 50:
        errors.append(f"Too many topics ({len(valid_topics)}). Maximum is 50.")
        return False, [], errors
    
    return True, valid_topics, []


def validate_api_key_format(provider: str, api_key: str) -> Tuple[bool, str]:
    """
    Validate API key format for specific providers
    
    Args:
        provider: Provider name (e.g., "openai", "pexels")
        api_key: API key to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not api_key or not api_key.strip():
        return False, "API key cannot be empty"
    
    provider = provider.lower()
    
    # OpenAI keys start with "sk-"
    if provider == "openai" and not api_key.startswith("sk-"):
        return False, "OpenAI API keys should start with 'sk-'"
    
    # Pexels keys are alphanumeric, typically 56 characters
    if provider == "pexels" and len(api_key) < 20:
        return False, "Pexels API key seems too short"
    
    # Basic length check for all keys
    if len(api_key) < 10:
        return False, "API key seems too short. Please check and try again."
    
    return True, ""


def sanitize_input(text: str, max_length: int = 10000) -> str:
    """
    Sanitize user input to prevent injection attacks
    
    Args:
        text: User input text
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Truncate to max length
    text = text[:max_length]
    
    # Remove null bytes
    text = text.replace("\x00", "")
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def validate_file_path(file_path: str, allowed_dir: str = None) -> Tuple[bool, str]:
    """
    Validate file path to prevent directory traversal
    
    Args:
        file_path: File path to validate
        allowed_dir: Optional directory path that file must be under
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    import os
    import pathlib
    
    if not file_path:
        return False, "File path is empty"
    
    # Check for path traversal attempts
    if ".." in file_path or file_path.startswith("/"):
        return False, "Invalid file path (potential directory traversal)"
    
    # If allowed_dir specified, ensure file is under that directory
    if allowed_dir:
        try:
            base = pathlib.Path(allowed_dir).resolve()
            target = (base / file_path).resolve()
            target.relative_to(base)  # Raises ValueError if not relative
        except (ValueError, Exception):
            return False, "File path outside allowed directory"
    
    return True, ""
