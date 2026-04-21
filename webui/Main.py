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

# Initialize logging configuration
from webui.logging_config import setup_webui_logging, log_system_info
setup_webui_logging()
log_system_info()

from app.config import config
from app.models.schema import (
    VideoAspect,
    VideoConcatMode,
    VideoParams,
    VideoTransitionMode,
)
from app.services import llm, voice
from app.utils import utils

# Import WebUI components
from webui.components.llm_config import render_llm_config
from webui.components.video_source_config import render_video_api_key_management
from webui.components.task_creation import (
    create_video_task_with_validation,
    create_bulk_tasks_with_progress,
    validate_and_show_params_summary
)
from webui.utils.constants import ConfigKeys, Defaults, SessionKeys
from webui.utils.validation import validate_file_path

st.set_page_config(
    page_title="MoneyPrinterTurbo",
    page_icon="💻",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': 'https://github.com/yourusername/MoneyPrinterTurbo-openai-tts',
        'Report a bug': 'https://github.com/yourusername/MoneyPrinterTurbo-openai-tts/issues',
        'About': '''### MoneyPrinterTurbo WebUI\n\nAutomated video creation platform with AI-powered scripting.\n\nVersion: 2.0\n\nGitHub: https://github.com/yourusername/MoneyPrinterTurbo-openai-tts'''
    }
)

is_dev_mode = (os.environ.get("MPT_MODE", "") or "").strip().lower() == "dev"

# Ultra-compact styling - eliminate wasted space
streamlit_style = """
<style>
    /* Reduce header height and padding */
    header[data-testid="stHeader"] {
        height: 2.5rem !important;
        min-height: 2.5rem !important;
    }
    /* Reduce top container padding - this was the issue! */
    .stMainBlockContainer.block-container,
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
    }
    /* Also target the specific class */
    div[class*="stMainBlockContainer"] {
        padding-top: 1rem !important;
    }
    /* Remove toolbar spacing */
    .stApp header {
        padding: 0 !important;
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
    # Compact header with language selector on the right
    col1, col2 = st.columns([6, 1])
    
    with col1:
        if is_dev_mode:
            st.markdown(
                '<h1 style="margin: 0; padding: 0;">💻 MoneyPrinterTurbo</h1>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<h1 style="margin: 0; padding: 0;">MoneyPrinterTurbo</h1>',
                unsafe_allow_html=True,
            )
    
    with col2:
        # Language selector with flag icons
        lang_options = {
            "zh-CN": "🇨🇳 中文",
            "en-US": "🇺🇸 EN",
            "zh-TW": "🇨🇳 繁體"
        }
        
        current_lang = config.ui.get("language", "en")
        lang_map_reverse = {"zh": "zh-CN", "en": "en-US", "zh-TW": "zh-TW"}
        current_key = lang_map_reverse.get(current_lang, "en-US")
        
        selected_language = st.selectbox(
            "Language",
            options=list(lang_options.keys()),
            format_func=lambda x: lang_options[x],
            index=list(lang_options.keys()).index(current_key),
            label_visibility="collapsed",
            key="language_selector"
        )
        
        language_map = {
            "zh-CN": "zh",
            "en-US": "en",
            "zh-TW": "zh-TW"
        }
        config.ui["language"] = language_map.get(selected_language, "zh")
    
    # ========================================================================
    # MAIN TABS - Create Video first, Config last
    # ========================================================================
    main_tabs = st.tabs([
        "🎬 " + tr("Create Video"),
        "📦 " + tr("Bulk Create"),
        "� " + tr("Script Library"),
        "� " + tr("Task Browser"),
        "⚙️ " + tr("Config")
    ])
    
    # ========================================================================
    # TAB 0: Single Video Creation
    # ========================================================================
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
        
        # Step 1: Input topic
        def on_subject_change():
            # Force rerun when subject changes to update button state
            pass
        
        video_subject = st.text_input(
            tr("Video Subject / Topic"),
            value=st.session_state.get(SessionKeys.VIDEO_SUBJECT, ""),
            help=tr("Enter topic or keywords for AI to generate script (press Enter to activate button)"),
            placeholder=tr("e.g., home improvement tips, AI technology, healthy cooking"),
            key="video_subject_input",
            on_change=on_subject_change
        )
        st.session_state[SessionKeys.VIDEO_SUBJECT] = video_subject
        
        # Generate Script button (enabled if subject has content)
        col1, col2 = st.columns([1, 3])
        with col1:
            generate_enabled = bool(video_subject and video_subject.strip())
            if st.button("✨ " + tr("Generate Script"), type="secondary", disabled=not generate_enabled, key="generate_script_btn"):
                if video_subject.strip():
                    with st.spinner(tr("Generating script with AI...")):
                        try:
                            import requests
                            
                            # Step 1: Generate script (increase timeout for slow Ollama models)
                            script_response = requests.post(
                                f"{_api_base_url()}/api/v1/scripts",
                                json={
                                    "video_subject": video_subject.strip(),
                                    "video_language": config.ui.get("language", "en"),
                                    "paragraph_number": config.ui.get(ConfigKeys.PARAGRAPH_NUMBER, Defaults.PARAGRAPH_NUMBER)
                                },
                                headers=_api_headers(),
                                timeout=180  # 3 minutes for Ollama model loading + generation
                            )
                            script_response.raise_for_status()
                            script_data = script_response.json()
                            generated_script = script_data.get("data", {}).get("video_script", "")
                            
                            if not generated_script:
                                st.error("❌ " + tr("No script generated"))
                            else:
                                st.session_state["generated_script"] = generated_script
                                
                                # Step 2: Generate global search terms
                                with st.spinner(tr("Generating global keywords...")):
                                    terms_response = requests.post(
                                        f"{_api_base_url()}/api/v1/terms",
                                        json={
                                            "video_subject": video_subject.strip(),
                                            "video_script": generated_script,
                                            "amount": 10
                                        },
                                        headers=_api_headers(),
                                        timeout=120  # 2 minutes for keyword generation
                                    )
                                    terms_response.raise_for_status()
                                    terms_data = terms_response.json()
                                    video_terms_list = terms_data.get("data", {}).get("video_terms", [])
                                    generated_terms = ", ".join(video_terms_list) if isinstance(video_terms_list, list) else str(video_terms_list)
                                    st.session_state["generated_terms"] = generated_terms
                                
                                # Initialize empty sentence keywords (user can generate manually later)
                                if "sentence_keywords" not in st.session_state:
                                    st.session_state["sentence_keywords"] = {}
                                
                                # Auto-save script to library
                                from webui.components.script_library import auto_save_script
                                script_id = auto_save_script(
                                    subject=video_subject.strip(),
                                    script=generated_script,
                                    keywords=video_terms_list if isinstance(video_terms_list, list) else [],
                                    language=config.ui.get("language", "en"),
                                    paragraph_number=config.ui.get(ConfigKeys.PARAGRAPH_NUMBER, Defaults.PARAGRAPH_NUMBER)
                                )
                                if script_id:
                                    st.session_state["current_script_id"] = script_id
                                    logger.info(f"Auto-saved script: {script_id}")
                                
                                st.success("✅ " + tr("Script and keywords generated successfully!"))
                                st.info("💾 " + tr("Script auto-saved to Script Library"))
                                st.rerun()
                        except requests.exceptions.HTTPError as e:
                            st.error(f"❌ API Error: {e.response.status_code} - {e.response.text}")
                            logger.exception("Script generation failed")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                            logger.exception("Script generation failed")
        
        with col2:
            st.caption("💡 " + tr("Click to generate script from your topic using AI"))
        
        st.divider()
        
        # Step 2: Review & Edit Generated Content
        st.subheader(tr("📝 Review Generated Content"))
        
        # View mode selector
        view_mode = st.radio(
            tr("Review Mode"),
            options=["Simple", "Sentence-Level"],
            horizontal=True,
            help=tr("Simple: Edit full script. Sentence-Level: Edit keywords per sentence for better clip matching")
        )
        
        if view_mode == "Simple":
            # Original simple view
            col1, col2 = st.columns(2)
            
            with col1:
                video_script = st.text_area(
                    tr("Video Script"),
                    value=st.session_state.get("generated_script", st.session_state.get(SessionKeys.VIDEO_SCRIPT, "")),
                    height=250,
                    help=tr("Review and edit the generated script")
                )
                st.session_state[SessionKeys.VIDEO_SCRIPT] = video_script
                params.video_script = video_script.strip()
            
            with col2:
                video_terms = st.text_area(
                    tr("Global Search Terms"),
                    value=st.session_state.get("generated_terms", st.session_state.get(SessionKeys.VIDEO_TERMS, "")),
                    height=250,
                    help=tr("Keywords used across entire video (comma-separated)")
                )
                st.session_state[SessionKeys.VIDEO_TERMS] = video_terms
                params.video_terms = video_terms.strip()
        
        else:
            # Sentence-level view
            st.info("💡 " + tr("Review each sentence and its keywords. Edit keywords to improve video clip matching."))
            
            # Get script and split into sentences
            full_script = st.session_state.get("generated_script", st.session_state.get(SessionKeys.VIDEO_SCRIPT, ""))
            
            if full_script:
                # Simple sentence splitter (can be improved with NLP)
                import re
                sentences = re.split(r'[.!?]+\s+', full_script.strip())
                sentences = [s.strip() for s in sentences if s.strip()]
                
                # Initialize sentence-level data if not exists
                if "sentence_keywords" not in st.session_state:
                    st.session_state["sentence_keywords"] = {}
                
                # Add manual keyword generation button
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.caption(f"📝 {len(sentences)} sentences detected")
                with col2:
                    if st.button("🔄 Generate All Keywords", use_container_width=True, type="primary"):
                        with st.spinner(tr("Generating keywords for each sentence...")):
                            for idx, sentence in enumerate(sentences):
                                # Use edited sentence if available
                                current_sentence = st.session_state.get(f"sentence_{idx}", sentence)
                                try:
                                    sent_terms_response = requests.post(
                                        f"{_api_base_url()}/api/v1/terms",
                                        json={
                                            "video_subject": current_sentence[:50],
                                            "video_script": current_sentence,
                                            "amount": 5
                                        },
                                        headers=_api_headers(),
                                        timeout=120
                                    )
                                    sent_terms_response.raise_for_status()
                                    sent_data = sent_terms_response.json()
                                    sent_terms_list = sent_data.get("data", {}).get("video_terms", [])
                                    st.session_state["sentence_keywords"][idx] = ", ".join(sent_terms_list) if isinstance(sent_terms_list, list) else ""
                                except Exception as e:
                                    logger.warning(f"Failed to generate keywords for sentence {idx}: {e}")
                                    st.session_state["sentence_keywords"][idx] = ""
                            st.success("✅ Keywords generated for all sentences!")
                            st.rerun()
                
                st.divider()
                
                # Display each sentence with editable keywords
                for idx, sentence in enumerate(sentences):
                    with st.expander(f"📌 Sentence {idx + 1}", expanded=idx < 3):
                        # Sentence text (editable)
                        edited_sentence = st.text_area(
                            tr("Sentence Text"),
                            value=sentence,
                            height=70,
                            key=f"sentence_{idx}",
                            label_visibility="collapsed"
                        )
                        
                        # Keywords for this sentence with regenerate button
                        kw_col1, kw_col2 = st.columns([4, 1])
                        with kw_col1:
                            default_keywords = st.session_state["sentence_keywords"].get(idx, "")
                            sentence_keywords = st.text_input(
                                tr("Keywords for this sentence"),
                                value=default_keywords,
                                placeholder=tr("e.g., home renovation, tools, construction"),
                                key=f"keywords_{idx}",
                                help=tr("Specific keywords for finding clips for this sentence")
                            )
                            st.session_state["sentence_keywords"][idx] = sentence_keywords
                        with kw_col2:
                            if st.button("🔄", key=f"regen_{idx}", help="Regenerate keywords for this sentence"):
                                st.session_state[f"regen_trigger_{idx}"] = True
                                st.rerun()
                        
                        # Handle regeneration trigger
                        if st.session_state.get(f"regen_trigger_{idx}", False):
                            st.session_state[f"regen_trigger_{idx}"] = False
                            try:
                                import requests as req
                                with st.spinner(f"Generating keywords for sentence {idx + 1}..."):
                                    sent_terms_response = req.post(
                                        f"{_api_base_url()}/api/v1/terms",
                                        json={
                                            "video_subject": edited_sentence[:50],
                                            "video_script": edited_sentence,
                                            "amount": 5
                                        },
                                        headers=_api_headers(),
                                        timeout=120
                                    )
                                    sent_terms_response.raise_for_status()
                                    sent_data = sent_terms_response.json()
                                    sent_terms_list = sent_data.get("data", {}).get("video_terms", [])
                                    st.session_state["sentence_keywords"][idx] = ", ".join(sent_terms_list) if isinstance(sent_terms_list, list) else ""
                                    st.success(f"✅ Keywords regenerated for sentence {idx + 1}")
                            except Exception as e:
                                st.error(f"❌ Failed: {str(e)}")
                        
                        # Show character/word count
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.caption(f"📝 {len(edited_sentence.split())} words")
                        with col2:
                            st.caption(f"🔤 {len(edited_sentence)} characters")
                        with col3:
                            st.caption(f"🏷️ {len(sentence_keywords.split(','))} keywords")
                
                # Reconstruct full script from edited sentences
                reconstructed_script = ". ".join([
                    st.session_state.get(f"sentence_{i}", s) 
                    for i, s in enumerate(sentences)
                ])
                st.session_state[SessionKeys.VIDEO_SCRIPT] = reconstructed_script
                params.video_script = reconstructed_script
                
                # Reconstruct terms (combine all sentence keywords)
                all_keywords = []
                for idx in range(len(sentences)):
                    kw = st.session_state["sentence_keywords"].get(idx, "")
                    if kw:
                        all_keywords.extend([k.strip() for k in kw.split(",") if k.strip()])
                
                # Remove duplicates while preserving order
                seen = set()
                unique_keywords = []
                for kw in all_keywords:
                    if kw.lower() not in seen:
                        seen.add(kw.lower())
                        unique_keywords.append(kw)
                
                combined_terms = ", ".join(unique_keywords)
                st.session_state[SessionKeys.VIDEO_TERMS] = combined_terms
                params.video_terms = combined_terms
                
                # Show summary
                st.divider()
                st.success(f"✅ {len(sentences)} sentences • {len(unique_keywords)} unique keywords")
                
                with st.expander("📋 View Combined Keywords", expanded=False):
                    st.code(combined_terms, language="text")
            else:
                st.warning("⚠️ " + tr("Generate a script first to use sentence-level editing"))
        
        st.divider()
        
        # Step 3: Create Video with approved content
        params.video_subject = video_subject.strip()
        
        # Create task button
        if st.button(tr("🎬 Create Video Task"), type="primary", use_container_width=True):
            if not params.video_script:
                st.error(tr("⚠️ Please generate or enter a script before creating video"))
            else:
                # CORRECT parameter order: api_base_url, api_headers, params
                task_data = create_video_task_with_validation(
                    _api_base_url(),
                    _api_headers(),
                    params
                )
                
                if task_data:
                    task_id = task_data.get("task_id", "")
                    st.session_state[SessionKeys.CURRENT_TASK_ID] = task_id
                    
                    # Link script to task if we have a script_id
                    if "current_script_id" in st.session_state:
                        from webui.components.script_library import link_script_to_task
                        script_id = st.session_state["current_script_id"]
                        if link_script_to_task(script_id, task_id):
                            logger.info(f"Linked script {script_id} to task {task_id}")
                    
                    # Show task details
                    with st.expander(tr("Task Details"), expanded=True):
                        st.json(task_data)
    
    # ========================================================================
    # TAB 1: Bulk Video Creation
    # ========================================================================
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
    
    # ========================================================================
    # TAB 2: Script Library
    # ========================================================================
    with main_tabs[2]:
        from webui.components.script_library import render_script_library
        render_script_library()
    
    # ========================================================================
    # TAB 3: Task Browser
    # ========================================================================
    with main_tabs[3]:
        from webui.components.task_browser import render_task_browser
        render_task_browser(_api_base_url(), _api_headers())
    
    # ========================================================================
    # TAB 4: Configuration
    # ========================================================================
    with main_tabs[4]:
        st.markdown("### " + tr("Configuration"))
        st.caption(tr("Configure LLM providers and advanced settings"))
        st.divider()
        
        # Configuration sub-tabs
        config_tabs = st.tabs([
            tr("LLM Provider"),
            tr("TTS Provider"),
            tr("Video API Keys"),
            tr("Advanced Settings")
        ])
        
        with config_tabs[0]:
            # LLM configuration
            render_llm_config()
        
        with config_tabs[1]:
            # TTS Provider configuration
            from webui.components.tts_provider_config import render_tts_provider_section
            render_tts_provider_section()
        
        with config_tabs[2]:
            # Video source API key management
            st.write(tr("Video Source API Keys"))
            st.caption(tr("Manage API keys for Pexels and Pixabay"))
            st.divider()
            render_video_api_key_management()
        
        with config_tabs[3]:
            # Advanced settings
            st.write(tr("Advanced Settings"))
            st.caption(tr("These settings are for advanced users"))
            
            # API Key for webui access
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
        
        # Save button
        if st.button("💾 " + tr("Save Configuration"), type="primary", use_container_width=True):
            config.save_config()
            st.success("✅ " + tr("Configuration saved successfully!"))


if __name__ == "__main__":
    try:
        logger.info("Starting MoneyPrinterTurbo WebUI")
        main()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        logger.exception("Unhandled exception in main()")
        raise
