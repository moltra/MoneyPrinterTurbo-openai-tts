"""
Internationalization (i18n) module for WebUI
Provides translation function that loads from JSON files
"""
import json
import os
from typing import Dict, Optional
from pathlib import Path

# Cache loaded translations
_translations: Dict[str, Dict[str, str]] = {}
_current_language = "en"


def load_language(lang: str = "en") -> Dict[str, str]:
    """Load translation file for given language"""
    global _translations
    
    if lang in _translations:
        return _translations[lang]
    
    i18n_dir = Path(__file__).parent
    lang_file = i18n_dir / f"{lang}.json"
    
    if not lang_file.exists():
        # Fallback to English
        lang = "en"
        lang_file = i18n_dir / "en.json"
    
    try:
        with open(lang_file, 'r', encoding='utf-8') as f:
            translations = json.load(f)
            _translations[lang] = translations
            return translations
    except Exception as e:
        print(f"Error loading language file {lang_file}: {e}")
        return {}


def set_language(lang: str):
    """Set current UI language"""
    global _current_language
    _current_language = lang
    load_language(lang)


def tr(key: str, lang: Optional[str] = None) -> str:
    """
    Translate a key to current language
    
    Args:
        key: Translation key (can be nested with dots, e.g., "config.save")
        lang: Optional language override
    
    Returns:
        Translated string or the key itself if not found
    """
    if lang is None:
        lang = _current_language
    
    translations = load_language(lang)
    
    # Handle nested keys (e.g., "config.save")
    if '.' in key:
        parts = key.split('.')
        value = translations
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return key  # Return key if path not found
        return value if isinstance(value, str) else key
    
    # Direct key lookup
    return translations.get(key, key)


# Initialize with English by default
load_language("en")
