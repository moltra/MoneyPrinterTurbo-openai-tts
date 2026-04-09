"""
Video Source Configuration Component
Secure configuration for Pexels and Pixabay API keys
"""
import streamlit as st
from typing import List

from app.config import config
from webui.i18n import tr
from webui.utils.security import render_secure_api_key_input, mask_sensitive_value


def _get_keys_from_config(cfg_key: str) -> List[str]:
    """Get API keys from config as list"""
    api_keys = config.app.get(cfg_key, [])
    if isinstance(api_keys, str):
        api_keys = [api_keys] if api_keys else []
    return api_keys


def _save_keys_to_config(cfg_key: str, value: str) -> None:
    """Save comma-separated API keys to config"""
    value = value.replace(" ", "")
    if value:
        keys = [k.strip() for k in value.split(",") if k.strip()]
        config.app[cfg_key] = keys
    else:
        config.app[cfg_key] = []


def render_video_source_config() -> None:
    """
    Render video source configuration with secure API key handling
    """
    st.write(tr("Video Source Settings"))
    
    # Pexels configuration
    pexels_keys = _get_keys_from_config("pexels_api_keys")
    
    # Show masked current keys
    if pexels_keys:
        display_value = ", ".join([mask_sensitive_value(k, visible_chars=4) for k in pexels_keys])
    else:
        display_value = ""
    
    pexels_input = st.text_input(
        tr("Pexels API Key"),
        value=display_value,
        type="password",
        help=tr("Enter one or more API keys separated by commas. Previously configured keys are shown masked.")
    )
    
    # Only update if user entered something different
    if pexels_input and not pexels_input.startswith("•"):
        _save_keys_to_config("pexels_api_keys", pexels_input)
    elif not pexels_input and pexels_keys:
        # User cleared all keys
        config.app["pexels_api_keys"] = []
    
    # Pixabay configuration
    pixabay_keys = _get_keys_from_config("pixabay_api_keys")
    
    # Show masked current keys
    if pixabay_keys:
        display_value = ", ".join([mask_sensitive_value(k, visible_chars=4) for k in pixabay_keys])
    else:
        display_value = ""
    
    pixabay_input = st.text_input(
        tr("Pixabay API Key"),
        value=display_value,
        type="password",
        help=tr("Enter one or more API keys separated by commas. Previously configured keys are shown masked.")
    )
    
    # Only update if user entered something different
    if pixabay_input and not pixabay_input.startswith("•"):
        _save_keys_to_config("pixabay_api_keys", pixabay_input)
    elif not pixabay_input and pixabay_keys:
        # User cleared all keys
        config.app["pixabay_api_keys"] = []
    
    # Save config
    config.save_config()


def render_video_api_key_management() -> None:
    """
    Render API key management panel (for advanced users)
    Allows adding/removing individual keys
    """
    st.subheader(tr("API Key Management"))
    st.caption(tr("Manage individual API keys for video sources"))
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Pexels API Keys**")
        pexels_keys = _get_keys_from_config("pexels_api_keys")
        
        if pexels_keys:
            st.write(tr("Current Keys:"))
            for i, key in enumerate(pexels_keys):
                # Show masked key
                st.code(mask_sensitive_value(key, visible_chars=8))
        else:
            st.info(tr("No Pexels API Keys currently configured"))
        
        new_pexels_key = st.text_input(
            tr("Add Pexels API Key"),
            type="password",
            key="pexels_new_key"
        )
        
        if st.button(tr("Add Pexels API Key")):
            if new_pexels_key and new_pexels_key not in pexels_keys:
                from webui.utils.validation import validate_api_key_format
                is_valid, error_msg = validate_api_key_format("pexels", new_pexels_key)
                
                if is_valid:
                    pexels_keys.append(new_pexels_key)
                    config.app["pexels_api_keys"] = pexels_keys
                    config.save_config()
                    st.success(tr("Pexels API Key added successfully"))
                    st.rerun()
                else:
                    st.error(error_msg)
            elif new_pexels_key in pexels_keys:
                st.warning(tr("This API Key already exists"))
            else:
                st.error(tr("Please enter a valid API Key"))
        
        if pexels_keys:
            # Show delete option with masked keys
            masked_keys = [f"Key {i+1}: ...{key[-8:]}" for i, key in enumerate(pexels_keys)]
            delete_index = st.selectbox(
                tr("Select Pexels API Key to delete"),
                range(len(pexels_keys)),
                format_func=lambda i: masked_keys[i],
                key="pexels_delete_key"
            )
            
            if st.button(tr("Delete Selected Pexels API Key")):
                pexels_keys.pop(delete_index)
                config.app["pexels_api_keys"] = pexels_keys
                config.save_config()
                st.success(tr("Pexels API Key deleted successfully"))
                st.rerun()
    
    with col2:
        st.write("**Pixabay API Keys**")
        pixabay_keys = _get_keys_from_config("pixabay_api_keys")
        
        if pixabay_keys:
            st.write(tr("Current Keys:"))
            for i, key in enumerate(pixabay_keys):
                # Show masked key
                st.code(mask_sensitive_value(key, visible_chars=8))
        else:
            st.info(tr("No Pixabay API Keys currently configured"))
        
        new_pixabay_key = st.text_input(
            tr("Add Pixabay API Key"),
            type="password",
            key="pixabay_new_key"
        )
        
        if st.button(tr("Add Pixabay API Key")):
            if new_pixabay_key and new_pixabay_key not in pixabay_keys:
                from webui.utils.validation import validate_api_key_format
                is_valid, error_msg = validate_api_key_format("pixabay", new_pixabay_key)
                
                if is_valid:
                    pixabay_keys.append(new_pixabay_key)
                    config.app["pixabay_api_keys"] = pixabay_keys
                    config.save_config()
                    st.success(tr("Pixabay API Key added successfully"))
                    st.rerun()
                else:
                    st.error(error_msg)
            elif new_pixabay_key in pixabay_keys:
                st.warning(tr("This API Key already exists"))
            else:
                st.error(tr("Please enter a valid API Key"))
        
        if pixabay_keys:
            # Show delete option with masked keys
            masked_keys = [f"Key {i+1}: ...{key[-8:]}" for i, key in enumerate(pixabay_keys)]
            delete_index = st.selectbox(
                tr("Select Pixabay API Key to delete"),
                range(len(pixabay_keys)),
                format_func=lambda i: masked_keys[i],
                key="pixabay_delete_key"
            )
            
            if st.button(tr("Delete Selected Pixabay API Key")):
                pixabay_keys.pop(delete_index)
                config.app["pixabay_api_keys"] = pixabay_keys
                config.save_config()
                st.success(tr("Pixabay API Key deleted successfully"))
                st.rerun()
