"""
TTS Provider Configuration Component
Comprehensive TTS provider selection and configuration
"""
import streamlit as st
from typing import Dict, List, Tuple

from app.config import config
from webui.i18n import tr
from webui.utils.security import render_secure_api_key_input


# TTS Provider definitions
TTS_PROVIDERS = {
    "edge": {
        "name": "Edge TTS (Microsoft)",
        "description": "Free, high-quality voices from Microsoft Edge",
        "cost": "Free",
        "requires_api_key": False,
        "requires_config": False,
        "voices_prefix": None,  # No prefix, standard voice names
    },
    "azure_v2": {
        "name": "Azure TTS v2 (Premium)",
        "description": "Premium Azure Text-to-Speech service",
        "cost": "Paid",
        "requires_api_key": True,
        "requires_config": True,
        "voices_prefix": "-V2",  # Voice names end with -V2
    },
    "openai": {
        "name": "OpenAI TTS",
        "description": "Official OpenAI TTS-1 and TTS-1-HD",
        "cost": "Paid",
        "requires_api_key": True,
        "requires_config": True,
        "voices_prefix": "openai:",
    },
    "alltalk": {
        "name": "AllTalk (GPU Accelerated)",
        "description": "Self-hosted, GPU-accelerated TTS (OpenAI compatible)",
        "cost": "Free (Self-hosted)",
        "requires_api_key": False,
        "requires_config": True,
        "voices_prefix": "openai:",
    },
    "siliconflow": {
        "name": "SiliconFlow TTS",
        "description": "Chinese TTS provider with multiple models",
        "cost": "Paid",
        "requires_api_key": True,
        "requires_config": True,
        "voices_prefix": "siliconflow:",
    },
    "gemini": {
        "name": "Google Gemini TTS",
        "description": "Google's Gemini Text-to-Speech API",
        "cost": "Free tier available",
        "requires_api_key": True,
        "requires_config": True,
        "voices_prefix": "gemini:",
    },
}

# Voice examples per provider
VOICE_EXAMPLES = {
    "edge": [
        "en-US-GuyNeural (Male, US English)",
        "en-US-AriaNeural (Female, US English)",
        "en-GB-RyanNeural (Male, UK English)",
        "zh-CN-XiaoxiaoNeural (Female, Chinese)",
    ],
    "azure_v2": [
        "en-US-GuyNeural-V2 (Male, US English)",
        "en-US-AriaNeural-V2 (Female, US English)",
    ],
    "openai": [
        "openai:alloy (Neutral)",
        "openai:echo (Male)",
        "openai:fable (British Male)",
        "openai:onyx (Deep Male)",
        "openai:nova (Female)",
        "openai:shimmer (Soft Female)",
    ],
    "alltalk": [
        "openai:voice_name (Check AllTalk UI for available voices)",
    ],
    "siliconflow": [
        "siliconflow:FishTTS:alex (Example format)",
    ],
    "gemini": [
        "gemini:Zephyr (Female)",
        "gemini:Puck (Male)",
        "gemini:Charon (Neutral)",
        "gemini:Kore (Female)",
    ],
}


def render_tts_provider_selector() -> str:
    """
    Render TTS provider selection UI
    Returns: selected provider key
    """
    st.markdown("### 🎤 TTS Provider Configuration")
    
    # Get current provider from config
    current_tts_provider = config.app.get("tts_provider", "").strip().lower()
    current_subtitle_provider = config.app.get("subtitle_provider", "edge").strip().lower()
    
    # Determine current provider
    if current_tts_provider in ["openai", "openai_style", "openai-tts"]:
        # Check if it's AllTalk or OpenAI
        base_url = config.app.get("openai_tts_base_url", "").strip()
        if "alltalk" in base_url.lower() or base_url.endswith(":7851") or base_url == "http://alltalk:7851/api/tts/generate":
            default_provider = "alltalk"
        else:
            default_provider = "openai"
    elif current_subtitle_provider == "edge":
        default_provider = "edge"
    else:
        default_provider = "edge"
    
    # Provider selection
    provider_options = []
    provider_keys = []
    for key, info in TTS_PROVIDERS.items():
        label = f"{info['name']} ({info['cost']})"
        provider_options.append(label)
        provider_keys.append(key)
    
    try:
        default_index = provider_keys.index(default_provider)
    except ValueError:
        default_index = 0
    
    selected_index = st.selectbox(
        "Select TTS Provider",
        range(len(provider_options)),
        format_func=lambda i: provider_options[i],
        index=default_index,
        key="tts_provider_select",
        help="Choose your preferred text-to-speech service"
    )
    
    selected_provider = provider_keys[selected_index]
    provider_info = TTS_PROVIDERS[selected_provider]
    
    # Show provider description
    st.info(f"**{provider_info['name']}**: {provider_info['description']}")
    
    # Show voice examples
    with st.expander("📋 Voice Examples", expanded=False):
        st.markdown("**Example voice names for this provider:**")
        for voice in VOICE_EXAMPLES.get(selected_provider, []):
            st.code(voice, language=None)
    
    return selected_provider


def render_provider_configuration(provider: str) -> None:
    """
    Render configuration UI for the selected provider
    """
    if provider == "edge":
        render_edge_config()
    elif provider == "azure_v2":
        render_azure_v2_config()
    elif provider == "openai":
        render_openai_tts_config()
    elif provider == "alltalk":
        render_alltalk_config()
    elif provider == "siliconflow":
        render_siliconflow_tts_config()
    elif provider == "gemini":
        render_gemini_config()


def render_edge_config() -> None:
    """Configure Edge TTS (default, no config needed)"""
    st.success("✅ Edge TTS is ready to use - no configuration needed!")
    st.markdown("""
    **Features:**
    - Free to use
    - High-quality voices
    - Multiple languages
    - No API key required
    
    **Usage:** Use standard voice names like `en-US-GuyNeural` or `en-US-AriaNeural`
    """)
    
    # Update config
    config.app["tts_provider"] = ""
    config.app["subtitle_provider"] = "edge"


def render_azure_v2_config() -> None:
    """Configure Azure TTS v2"""
    st.write("**Azure TTS v2 Configuration**")
    
    saved_key = config.azure.get("speech_key", "")
    saved_region = config.azure.get("speech_region", "")
    
    # Secure API key input
    was_updated, new_api_key = render_secure_api_key_input(
        label="Azure Speech API Key",
        config_key="azure.speech_key",
        help_text=tr("Get your key from Azure Portal"),
        key="azure_speech_key_input"
    )
    
    if was_updated:
        if new_api_key:
            if not hasattr(config, 'azure'):
                config.azure = {}
            config.azure["speech_key"] = new_api_key
        else:
            if hasattr(config, 'azure'):
                config.azure.pop("speech_key", None)
    
    # Region
    azure_region = st.text_input(
        "Azure Region",
        value=saved_region,
        key="azure_region_input",
        help="e.g., eastus, westeurope"
    )
    
    if not hasattr(config, 'azure'):
        config.azure = {}
    config.azure["speech_region"] = azure_region
    
    st.info("**Usage:** Add `-V2` to voice names, e.g., `en-US-GuyNeural-V2`")


def render_openai_tts_config() -> None:
    """Configure OpenAI TTS"""
    st.write("**OpenAI TTS Configuration**")
    
    saved_base_url = config.app.get("openai_tts_base_url", "https://api.openai.com/v1")
    saved_model = config.app.get("openai_tts_model_name", "tts-1")
    
    # Secure API key input
    was_updated, new_api_key = render_secure_api_key_input(
        label="OpenAI API Key",
        config_key="openai_tts_api_key",
        help_text=tr("Get your key from platform.openai.com"),
        key="openai_tts_api_key_input"
    )
    
    if was_updated:
        if new_api_key:
            config.app["openai_tts_api_key"] = new_api_key
        else:
            config.app.pop("openai_tts_api_key", None)
    
    # Base URL
    openai_base_url = st.text_input(
        "Base URL",
        value=saved_base_url,
        key="openai_tts_base_url_input",
        help="Default: https://api.openai.com/v1"
    )
    
    # Model selection
    model_options = ["tts-1", "tts-1-hd"]
    try:
        default_model_index = model_options.index(saved_model)
    except ValueError:
        default_model_index = 0
    
    model_name = st.selectbox(
        "Model",
        model_options,
        index=default_model_index,
        key="openai_tts_model_select",
        help="tts-1-hd has higher quality but costs more"
    )
    
    # Update config
    config.app["tts_provider"] = "openai"
    config.app["openai_tts_base_url"] = openai_base_url
    config.app["openai_tts_model_name"] = model_name
    
    st.info("**Usage:** Use format `openai:alloy`, `openai:echo`, `openai:fable`, etc.")


def render_alltalk_config() -> None:
    """Configure AllTalk TTS"""
    st.write("**AllTalk TTS Configuration**")
    
    saved_url = config.app.get("openai_tts_base_url", "http://alltalk:7851/api/tts/generate")
    
    # AllTalk endpoint
    alltalk_url = st.text_input(
        "AllTalk Endpoint",
        value=saved_url,
        key="alltalk_url_input",
        help="Default: http://alltalk:7851/api/tts/generate"
    )
    
    # Check connection
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("Test Connection", key="test_alltalk"):
            st.info("Testing connection to AllTalk...")
            # Could add actual connection test here
    
    # Update config
    config.app["tts_provider"] = "openai"  # AllTalk uses OpenAI-compatible API
    config.app["openai_tts_base_url"] = alltalk_url
    config.app["openai_tts_api_key"] = "not-needed"  # AllTalk doesn't need API key
    
    st.success("✅ AllTalk uses GPU acceleration if available!")
    st.info("""
    **Features:**
    - Free (self-hosted)
    - GPU accelerated
    - OpenAI-compatible API
    - Custom voice models
    
    **Usage:** Use format `openai:voice_name` where voice_name matches your AllTalk voices
    """)
    st.markdown("**Tip:** Check AllTalk UI at http://alltalk:7851 to see available voices")


def render_siliconflow_tts_config() -> None:
    """Configure SiliconFlow TTS"""
    st.write("**SiliconFlow TTS Configuration**")
    
    # Secure API key input
    was_updated, new_api_key = render_secure_api_key_input(
        label="SiliconFlow API Key",
        config_key="siliconflow.api_key",
        help_text=tr("Get your key from SiliconFlow dashboard"),
        key="siliconflow_api_key_input"
    )
    
    if was_updated:
        if new_api_key:
            if not hasattr(config, 'siliconflow') or config.siliconflow is None:
                config.siliconflow = {}
            config.siliconflow["api_key"] = new_api_key
        else:
            if hasattr(config, 'siliconflow') and config.siliconflow:
                config.siliconflow.pop("api_key", None)
    
    # Update config
    config.app["tts_provider"] = ""  # Auto-detected from voice name
    
    st.info("""
    **Usage:** Use format `siliconflow:model:voice`
    
    Example: `siliconflow:FishTTS:alex`
    
    **Parameters:**
    - Voice Rate: 0.5-2.0 (speaking speed)
    - Voice Pitch: 0.5-2.0 (maps to pitch -20 to +20)
    - Volume: Default 1.0 (gain 0)
    """)


def render_gemini_config() -> None:
    """Configure Google Gemini TTS"""
    st.write("**Google Gemini TTS Configuration**")
    
    saved_api_key = config.app.get("gemini_api_key", "")
    
    # Secure API key input
    was_updated, new_api_key = render_secure_api_key_input(
        label="Gemini API Key",
        config_key="gemini_api_key",
        help_text=tr("Get your key from Google AI Studio"),
        key="gemini_api_key_input"
    )
    
    if was_updated:
        if new_api_key:
            config.app["gemini_api_key"] = new_api_key
        else:
            config.app.pop("gemini_api_key", None)
    
    # Update config
    config.app["tts_provider"] = ""  # Auto-detected from voice name
    
    st.info("""
    **Available Voices:**
    - `gemini:Zephyr` (Female)
    - `gemini:Puck` (Male)
    - `gemini:Charon` (Neutral)
    - `gemini:Kore` (Female)
    
    **Features:**
    - Free tier available
    - High quality
    - Multiple voice options
    """)


def render_tts_provider_section() -> None:
    """
    Main function to render complete TTS provider configuration section
    """
    st.markdown("---")
    
    # Provider selection
    selected_provider = render_tts_provider_selector()
    
    st.markdown("---")
    
    # Provider-specific configuration
    render_provider_configuration(selected_provider)
    
    # Save settings
    if st.button("💾 Save TTS Configuration", key="save_tts_config", type="primary"):
        config.save()
        st.success("✅ TTS configuration saved!")
        st.balloons()
