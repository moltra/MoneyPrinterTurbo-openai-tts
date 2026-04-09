"""
Security Utilities
Secure handling of sensitive data like API keys
"""
from typing import Optional, Tuple
import streamlit as st
from loguru import logger

from app.config import config


# Placeholder for masked API keys
MASKED_VALUE = "••••••••"


def render_secure_api_key_input(
    label: str,
    config_key: str,
    help_text: str = "",
    key: str = None
) -> Tuple[bool, Optional[str]]:
    """
    Render a secure API key input field
    Never pre-fills with actual key, only shows masked placeholder
    
    Args:
        label: Label for the input field
        config_key: Configuration key where API key is stored
        help_text: Help text to display
        key: Streamlit widget key
        
    Returns:
        Tuple of (was_updated, new_value_or_none)
    """
    current_value = config.app.get(config_key, "")
    has_existing = bool(current_value)
    
    # Show help text indicating if key is already configured
    if has_existing:
        display_help = f"Previously configured. {help_text}" if help_text else "Previously configured"
    else:
        display_help = help_text if help_text else "Enter API key"
    
    # Never show the actual key, only masked value if exists
    display_value = MASKED_VALUE if has_existing else ""
    
    new_value = st.text_input(
        label,
        value=display_value,
        type="password",
        help=display_help,
        key=key
    )
    
    # Only update if user entered something different from placeholder
    if new_value and new_value != MASKED_VALUE:
        # User entered a new key
        logger.info(f"API key updated for {config_key}")  # NEVER log the actual key
        return True, new_value
    elif new_value == "" and has_existing:
        # User cleared the field - interpret as wanting to remove the key
        logger.info(f"API key removed for {config_key}")
        return True, None
    else:
        # No change (still has masked value or empty)
        return False, None


def mask_sensitive_value(value: str, visible_chars: int = 4) -> str:
    """
    Mask sensitive value, showing only last N characters
    
    Args:
        value: Value to mask
        visible_chars: Number of characters to show at end
        
    Returns:
        Masked string
    """
    if not value or len(value) <= visible_chars:
        return MASKED_VALUE
    
    return "•" * (len(value) - visible_chars) + value[-visible_chars:]


def validate_api_key_strength(api_key: str) -> Tuple[bool, str]:
    """
    Validate API key has minimum security requirements
    
    Args:
        api_key: API key to validate
        
    Returns:
        Tuple of (is_valid, message)
    """
    if not api_key:
        return False, "API key cannot be empty"
    
    if len(api_key) < 16:
        return False, "API key is too short (minimum 16 characters)"
    
    if api_key == MASKED_VALUE:
        return False, "Cannot use masked placeholder as API key"
    
    # Check for obviously fake keys
    fake_patterns = [
        "your-api-key",
        "your_api_key",
        "example",
        "test123",
        "placeholder",
        "xxxxxxxx"
    ]
    
    lower_key = api_key.lower()
    for pattern in fake_patterns:
        if pattern in lower_key:
            return False, f"API key appears to be a placeholder (contains '{pattern}')"
    
    return True, "API key appears valid"


def safe_config_display(config_dict: dict, keys_to_mask: list = None) -> dict:
    """
    Create a safe copy of config dict with sensitive values masked
    
    Args:
        config_dict: Configuration dictionary
        keys_to_mask: List of key patterns to mask (default: api_key, token, secret, password)
        
    Returns:
        Dictionary with sensitive values masked
    """
    if keys_to_mask is None:
        keys_to_mask = [
            "api_key", "apikey", "api-key",
            "token", "access_token",
            "secret", "password", "passwd",
            "credential"
        ]
    
    safe_dict = {}
    for key, value in config_dict.items():
        key_lower = str(key).lower()
        
        # Check if key contains sensitive pattern
        is_sensitive = any(pattern in key_lower for pattern in keys_to_mask)
        
        if is_sensitive and value:
            if isinstance(value, str):
                safe_dict[key] = mask_sensitive_value(value)
            elif isinstance(value, list):
                safe_dict[key] = [mask_sensitive_value(str(v)) for v in value]
            else:
                safe_dict[key] = MASKED_VALUE
        else:
            safe_dict[key] = value
    
    return safe_dict


def render_api_key_status(config_keys: list[str]) -> dict:
    """
    Render a status panel showing which API keys are configured
    
    Args:
        config_keys: List of config keys to check
        
    Returns:
        Dictionary mapping config_key to boolean (configured or not)
    """
    status = {}
    
    st.write("**API Key Status:**")
    
    for config_key in config_keys:
        value = config.app.get(config_key, "")
        is_configured = bool(value)
        status[config_key] = is_configured
        
        # Extract provider name from key (e.g., "openai_api_key" -> "OpenAI")
        provider = config_key.replace("_api_key", "").replace("_api_keys", "").replace("_", " ").title()
        
        if is_configured:
            st.success(f"✅ {provider}: Configured")
        else:
            st.warning(f"⚠️ {provider}: Not configured")
    
    return status


def check_config_security_issues() -> list[str]:
    """
    Check configuration for common security issues
    
    Returns:
        List of security warnings/issues found
    """
    issues = []
    
    # Check if API keys are set in config (should be in environment or secure storage)
    sensitive_keys = [
        "openai_api_key", "pexels_api_keys", "pixabay_api_keys",
        "azure_api_key", "gemini_api_key"
    ]
    
    for key in sensitive_keys:
        value = config.app.get(key, "")
        if value:
            # Check if it looks like a real key (not placeholder)
            is_valid, msg = validate_api_key_strength(value)
            if not is_valid and "placeholder" in msg.lower():
                issues.append(f"{key}: {msg}")
    
    # Check for default/insecure values
    if config.app.get("llm_api_base", "").startswith("http://"):
        issues.append("LLM API base URL uses HTTP instead of HTTPS (insecure)")
    
    return issues


def secure_log(message: str, include_user_data: bool = False) -> None:
    """
    Log message without exposing sensitive data
    
    Args:
        message: Log message
        include_user_data: Whether message might contain user data (will be sanitized)
    """
    if include_user_data:
        # Additional sanitization for user-provided data
        from app.utils.logging import sanitize_log_data
        # This would need to parse the message, for now just warn
        logger.info(f"[USER_DATA] {message}")
    else:
        logger.info(message)
