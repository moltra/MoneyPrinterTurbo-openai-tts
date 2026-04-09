"""
Voice/TTS Configuration Component
Secure configuration for voice providers including OpenAI TTS and SiliconFlow
"""
import streamlit as st

from app.config import config
from webui.i18n import tr
from webui.utils.security import render_secure_api_key_input


def render_openai_tts_config() -> None:
    """
    Render OpenAI TTS configuration with secure API key handling
    """
    st.write("**OpenAI TTS Settings**")
    
    saved_base_url = config.app.get("openai_tts_base_url", "")
    saved_model_name = config.app.get("openai_tts_model_name", "")
    saved_voice = config.app.get("openai_tts_voice", "")
    
    # Base URL
    openai_tts_base_url = st.text_input(
        "OpenAI TTS Base URL",
        value=saved_base_url,
        key="openai_tts_base_url_input",
        help=tr("Leave empty for default OpenAI endpoint")
    )
    
    # Secure API key input
    was_updated, new_api_key = render_secure_api_key_input(
        label="OpenAI TTS API Key",
        config_key="openai_tts_api_key",
        help_text=tr("Required for OpenAI TTS service"),
        key="openai_tts_api_key_input"
    )
    
    if was_updated:
        if new_api_key:
            config.app["openai_tts_api_key"] = new_api_key
        else:
            config.app.pop("openai_tts_api_key", None)
    
    # Model name
    openai_tts_model_name = st.text_input(
        "OpenAI TTS Model Name",
        value=saved_model_name,
        key="openai_tts_model_name_input",
        help=tr("e.g., tts-1 or tts-1-hd")
    )
    
    # Voice selection
    openai_tts_voice = st.text_input(
        "OpenAI TTS Voice",
        value=saved_voice,
        key="openai_tts_voice_input",
        help=tr("e.g., alloy, echo, fable, onyx, nova, shimmer")
    )
    
    # Update config
    config.app["openai_tts_base_url"] = openai_tts_base_url
    config.app["openai_tts_model_name"] = openai_tts_model_name
    config.app["openai_tts_voice"] = openai_tts_voice


def render_siliconflow_config() -> None:
    """
    Render SiliconFlow TTS configuration with secure API key handling
    """
    st.write("**SiliconFlow Settings**")
    
    # Secure API key input
    was_updated, new_api_key = render_secure_api_key_input(
        label=tr("SiliconFlow API Key"),
        config_key="siliconflow.api_key",
        help_text=tr("Required for SiliconFlow TTS service"),
        key="siliconflow_api_key_input"
    )
    
    if was_updated:
        if new_api_key:
            if "api_key" not in config.siliconflow:
                config.siliconflow = {}
            config.siliconflow["api_key"] = new_api_key
        else:
            if "siliconflow" in config.__dict__:
                config.siliconflow.pop("api_key", None)
    
    # Show SiliconFlow info
    st.info(
        tr("Rate: Uses Voice Rate setting, 0.5-2.0 maps to speaking_rate 0.5-2.0") + "\n" +
        tr("Pitch: Uses Voice Pitch setting, 0.5-2.0 maps to pitch -20 to +20") + "\n" +
        tr("Volume: Uses Speech Volume setting, default 1.0 maps to gain 0")
    )
