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
    # Convert list to comma-separated string for display
    pexels_keys = _get_keys_from_config("pexels_api_keys")
    # Store joined value temporarily so render_secure_api_key_input can read it
    config.app["pexels_api_keys_joined"] = ", ".join(pexels_keys) if pexels_keys else ""
    
    was_updated_pexels, new_pexels = render_secure_api_key_input(
        label=tr("Pexels API Key"),
        config_key="pexels_api_keys_joined",
        help_text=tr("Enter one or more API keys separated by commas"),
        key="pexels_api_key_input"
    )
    
    if was_updated_pexels:
        if new_pexels:
            _save_keys_to_config("pexels_api_keys", new_pexels)
        else:
            config.app["pexels_api_keys"] = []
        # Clean up temp key
        config.app.pop("pexels_api_keys_joined", None)
    
    # Pixabay configuration
    pixabay_keys = _get_keys_from_config("pixabay_api_keys")
    # Store joined value temporarily so render_secure_api_key_input can read it
    config.app["pixabay_api_keys_joined"] = ", ".join(pixabay_keys) if pixabay_keys else ""
    
    was_updated_pixabay, new_pixabay = render_secure_api_key_input(
        label=tr("Pixabay API Key"),
        config_key="pixabay_api_keys_joined",
        help_text=tr("Enter one or more API keys separated by commas"),
        key="pixabay_api_key_input"
    )
    
    if was_updated_pixabay:
        if new_pixabay:
            _save_keys_to_config("pixabay_api_keys", new_pixabay)
        else:
            config.app["pixabay_api_keys"] = []
        # Clean up temp key
        config.app.pop("pixabay_api_keys_joined", None)
    
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
