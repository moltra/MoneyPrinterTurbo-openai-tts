"""
Script Library Component
UI for viewing, searching, and managing generated scripts
"""
import streamlit as st
from datetime import datetime
from typing import Optional, Dict, Any
from loguru import logger

from webui.i18n import tr
from webui.services.script_storage import get_script_storage
from app.models.schema import VideoParams


def render_script_library():
    """
    Render the script library interface
    Shows all saved scripts with search, filter, and management options
    """
    storage = get_script_storage()
    
    # Header with statistics
    stats = storage.get_statistics()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(tr("Total Scripts"), stats["total"])
    with col2:
        st.metric(tr("Draft"), stats["draft"])
    with col3:
        st.metric(tr("Used"), stats["used"])
    with col4:
        st.metric(tr("Edited"), stats["edited"])
    
    st.divider()
    
    # Search and filter controls
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_query = st.text_input(
            tr("Search scripts"),
            placeholder=tr("Search by subject, keywords, or content..."),
            key="script_search"
        )
    
    with col2:
        status_filter = st.selectbox(
            tr("Filter by status"),
            options=["all", "draft", "used", "abandoned"],
            format_func=lambda x: tr(x.title()),
            key="script_status_filter"
        )
    
    with col3:
        sort_order = st.selectbox(
            tr("Sort by"),
            options=["newest", "oldest", "subject"],
            format_func=lambda x: tr(x.title()),
            key="script_sort"
        )
    
    st.divider()
    
    # Fetch scripts
    if search_query:
        scripts = storage.search_scripts(search_query)
    else:
        status = None if status_filter == "all" else status_filter
        scripts = storage.list_scripts(status=status, limit=100)
    
    # Apply sorting
    if sort_order == "oldest":
        scripts = list(reversed(scripts))
    elif sort_order == "subject":
        scripts = sorted(scripts, key=lambda s: s.get("subject", "").lower())
    
    # Display scripts
    if not scripts:
        st.info(tr("No scripts found"))
        st.caption(tr("Generate your first script in the Create Video tab"))
    else:
        st.caption(f"{len(scripts)} {tr('scripts found')}")
        
        for script in scripts:
            render_script_card(script)


def render_script_card(script: Dict[str, Any]):
    """
    Render a single script card
    
    Args:
        script: Script data dictionary
    """
    storage = get_script_storage()
    
    script_id = script.get("script_id", "")
    subject = script.get("subject", "Untitled")
    status = script.get("status", "draft")
    edited = script.get("edited", False)
    generated_at = script.get("generated_at", "")
    
    # Format timestamp
    try:
        dt = datetime.fromisoformat(generated_at)
        time_str = dt.strftime("%Y-%m-%d %H:%M")
    except:
        time_str = generated_at
    
    # Status icons
    status_icons = {
        "draft": "✏️",
        "used": "✅",
        "abandoned": "🗑️"
    }
    icon = status_icons.get(status, "📝")
    
    # Build title
    title = f"{icon} **{subject[:60]}{'...' if len(subject) > 60 else ''}**"
    if edited:
        title += " ✎"  # Pencil icon for edited
    
    # Create expandable card
    with st.expander(title, expanded=False):
        # Metadata row
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.caption(f"**{tr('Created')}:** {time_str}")
        
        with col2:
            st.caption(f"**{tr('Status')}:** {tr(status.title())}")
        
        with col3:
            task_count = len(script.get("task_ids", []))
            st.caption(f"**{tr('Videos')}:** {task_count}")
        
        st.divider()
        
        # Tabs for script details
        tabs = st.tabs([
            tr("Script"),
            tr("Keywords"),
            tr("Actions")
        ])
        
        with tabs[0]:
            render_script_content(script_id, script)
        
        with tabs[1]:
            render_script_keywords(script)
        
        with tabs[2]:
            render_script_actions(script_id, script)


def render_script_content(script_id: str, script: Dict[str, Any]):
    """
    Render script content with editing capability
    
    Args:
        script_id: Script identifier
        script: Script data
    """
    storage = get_script_storage()
    
    # Show full subject
    st.write(f"**{tr('Subject')}:** {script.get('subject', 'N/A')}")
    
    # Script text area (editable)
    current_script = script.get("script", "")
    
    edited_script = st.text_area(
        tr("Script Content"),
        value=current_script,
        height=300,
        key=f"script_content_{script_id}"
    )
    
    # Save button if changed
    if edited_script != current_script:
        if st.button(tr("Save Changes"), key=f"save_{script_id}", type="primary"):
            if storage.update_script(script_id, {"script": edited_script}):
                st.success(tr("Script updated successfully"))
                st.rerun()
            else:
                st.error(tr("Failed to update script"))
    
    # Metadata
    st.caption(f"**{tr('Language')}:** {script.get('language', 'N/A')}")
    st.caption(f"**{tr('Paragraphs')}:** {script.get('paragraph_number', 1)}")
    
    if script.get("edited"):
        st.caption("✎ " + tr("This script has been edited"))


def render_script_keywords(script: Dict[str, Any]):
    """
    Render script keywords
    
    Args:
        script: Script data
    """
    keywords = script.get("keywords", [])
    
    if not keywords:
        st.info(tr("No keywords for this script"))
    else:
        st.write(f"**{tr('Search Keywords')}:** ({len(keywords)} {tr('total')})")
        
        # Display as tags
        keyword_html = " ".join([
            f'<span style="background-color: #e0e0e0; padding: 4px 8px; margin: 2px; border-radius: 4px; display: inline-block;">{kw}</span>'
            for kw in keywords
        ])
        st.markdown(keyword_html, unsafe_allow_html=True)


def render_script_actions(script_id: str, script: Dict[str, Any]):
    """
    Render action buttons for script management
    
    Args:
        script_id: Script identifier
        script: Script data
    """
    storage = get_script_storage()
    status = script.get("status", "draft")
    
    st.write(f"**{tr('Script Actions')}:**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Create Video button
        if st.button(
            "🎬 " + tr("Create Video"),
            key=f"create_video_{script_id}",
            type="primary",
            use_container_width=True
        ):
            # Store script in session state for Create Video tab
            st.session_state.selected_script_id = script_id
            st.session_state.video_subject = script.get("subject", "")
            st.session_state.video_script = script.get("script", "")
            st.session_state.video_terms_list = script.get("keywords", [])
            
            # Switch to Create Video tab
            st.success(tr("Script loaded! Switch to Create Video tab to continue."))
            st.info(tr("The script and keywords have been loaded into the Create Video form."))
    
    with col2:
        # Change status dropdown
        new_status = st.selectbox(
            tr("Change Status"),
            options=["draft", "used", "abandoned"],
            index=["draft", "used", "abandoned"].index(status),
            key=f"status_{script_id}",
            format_func=lambda x: tr(x.title())
        )
        
        if new_status != status:
            if st.button(tr("Update Status"), key=f"update_status_{script_id}", use_container_width=True):
                if storage.update_script(script_id, {"status": new_status}):
                    st.success(tr("Status updated"))
                    st.rerun()
    
    with col3:
        # Delete button
        if st.button(
            "🗑️ " + tr("Delete"),
            key=f"delete_{script_id}",
            type="secondary",
            use_container_width=True
        ):
            # Confirmation
            if f"confirm_delete_{script_id}" not in st.session_state:
                st.session_state[f"confirm_delete_{script_id}"] = True
                st.warning(tr("Click Delete again to confirm"))
                st.rerun()
            else:
                if storage.delete_script(script_id):
                    st.success(tr("Script deleted"))
                    del st.session_state[f"confirm_delete_{script_id}"]
                    st.rerun()
                else:
                    st.error(tr("Failed to delete script"))
    
    # Linked tasks
    task_ids = script.get("task_ids", [])
    if task_ids:
        st.divider()
        st.write(f"**{tr('Linked Video Tasks')}:**")
        for task_id in task_ids:
            st.code(task_id, language="text")
            st.caption(tr("View in Task Browser tab"))


def auto_save_script(subject: str, script: str, keywords: list, language: str = "en", paragraph_number: int = 1) -> Optional[str]:
    """
    Auto-save a generated script to the library
    
    This should be called whenever a script is generated in the Create Video tab
    
    Args:
        subject: Video subject
        script: Generated script text
        keywords: Generated keywords list
        language: Script language
        paragraph_number: Number of paragraphs
        
    Returns:
        script_id if successful, None otherwise
    """
    try:
        storage = get_script_storage()
        
        script_id = storage.save_script(
            subject=subject,
            script=script,
            keywords=keywords,
            language=language,
            paragraph_number=paragraph_number
        )
        
        logger.info(f"Auto-saved script: {script_id} - {subject}")
        return script_id
    
    except Exception as e:
        logger.error(f"Failed to auto-save script: {e}")
        return None


def link_script_to_task(script_id: str, task_id: str) -> bool:
    """
    Link a script to a created video task
    
    This should be called when a video task is created from a script
    
    Args:
        script_id: Script identifier
        task_id: Task identifier
        
    Returns:
        True if successful, False otherwise
    """
    try:
        storage = get_script_storage()
        success = storage.mark_as_used(script_id, task_id)
        
        if success:
            logger.info(f"Linked script {script_id} to task {task_id}")
        
        return success
    
    except Exception as e:
        logger.error(f"Failed to link script to task: {e}")
        return False


def get_script_for_task(task_id: str) -> Optional[Dict[str, Any]]:
    """
    Find the script associated with a task
    
    Args:
        task_id: Task identifier
        
    Returns:
        Script data if found, None otherwise
    """
    try:
        storage = get_script_storage()
        scripts = storage.list_scripts(limit=1000)
        
        for script in scripts:
            if task_id in script.get("task_ids", []):
                return script
        
        return None
    
    except Exception as e:
        logger.error(f"Failed to get script for task: {e}")
        return None
