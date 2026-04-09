"""
WebUI Constants
Centralized constants for configuration keys, session state keys, and default values
"""


class ConfigKeys:
    """Configuration file keys"""
    # Video settings
    VIDEO_CLIP_DURATION = "video_clip_duration"
    VIDEO_COUNT = "video_count"
    VIDEO_SOURCE = "video_source"
    VIDEO_ASPECT = "video_aspect"
    VIDEO_CONCAT_MODE = "video_concat_mode"
    VIDEO_TRANSITION = "video_transition"
    
    # LLM settings
    LLM_PROVIDER = "llm_provider"
    LLM_MODEL_NAME = "llm_model_name"
    LLM_API_BASE = "llm_api_base"
    
    # Audio settings
    VOICE_NAME = "voice_name"
    VOICE_RATE = "voice_rate"
    VOICE_VOLUME = "voice_volume"
    VOICE_PITCH = "voice_pitch"
    BGM_TYPE = "bgm_type"
    BGM_FILE = "bgm_file"
    BGM_VOLUME = "bgm_volume"
    
    # Subtitle settings
    SUBTITLE_ENABLED = "subtitle_enabled"
    SUBTITLE_POSITION = "subtitle_position"
    FONT_NAME = "font_name"
    FONT_SIZE = "font_size"
    TEXT_FORE_COLOR = "text_fore_color"
    TEXT_BACKGROUND_COLOR = "text_background_color"
    STROKE_COLOR = "stroke_color"
    STROKE_WIDTH = "stroke_width"
    
    # Advanced settings
    N_THREADS = "n_threads"
    PARAGRAPH_NUMBER = "paragraph_number"
    SENTENCE_LEVEL_CLIPS = "sentence_level_clips"


class SessionKeys:
    """Session state keys"""
    # Video content
    VIDEO_SUBJECT = "video_subject"
    VIDEO_SCRIPT = "video_script"
    VIDEO_TERMS = "video_terms"
    VIDEO_LANGUAGE = "video_language"
    
    # UI state
    UI_LANGUAGE = "ui_language"
    SELECTED_CLIP_URLS = "selected_clip_urls"
    PREVIEW_ITEMS = "preview_items"
    REVIEW_ITEMS = "review_items"
    
    # Task state
    CURRENT_TASK_ID = "current_task_id"
    TASK_LIST_PAGE = "task_page"
    
    # Bulk operations
    BULK_TOPICS = "bulk_topics"
    BULK_CREATED = "bulk_created"
    BULK_FAILED = "bulk_failed"
    
    # Config state
    CONFIG_DIRTY = "config_dirty"
    CONFIG_HISTORY = "config_history"
    
    # App state
    APP_STATE = "app_state"


class Defaults:
    """Default values"""
    # Video
    CLIP_DURATION = 4
    VIDEO_COUNT = 5
    VIDEO_SOURCE = "pexels"
    VIDEO_ASPECT = "16:9"
    VIDEO_CONCAT_MODE = "random"
    VIDEO_TRANSITION = "none"
    
    # LLM
    LLM_PROVIDER = "OpenAI"
    LLM_MODEL = "gpt-3.5-turbo"
    
    # Voice
    VOICE_NAME = "en-US-JennyNeural"
    VOICE_RATE = 1.0
    VOICE_VOLUME = 1.0
    VOICE_PITCH = 1.0
    
    # BGM
    BGM_TYPE = "random"
    BGM_VOLUME = 0.3
    
    # Subtitle
    SUBTITLE_ENABLED = True
    SUBTITLE_POSITION = "bottom"
    FONT_NAME = "STHeitiMedium.ttc"
    FONT_SIZE = 60
    TEXT_FORE_COLOR = "#FFFFFF"
    TEXT_BACKGROUND_COLOR = "transparent"
    STROKE_COLOR = "#000000"
    STROKE_WIDTH = 1.5
    
    # Advanced
    N_THREADS = 2
    PARAGRAPH_NUMBER = 1
    SENTENCE_LEVEL_CLIPS = False
    
    # Task browser
    TASKS_PER_PAGE = 10
    MAX_TASK_HISTORY = 100


class UIMessages:
    """User-facing messages that should be translated"""
    # Errors
    ERROR_EMPTY_SUBJECT = "Video subject is required"
    ERROR_EMPTY_SCRIPT = "Either subject or script is required"
    ERROR_API_KEY_MISSING = "API key is required for selected provider"
    ERROR_NETWORK = "Network error. Please check your connection"
    ERROR_INVALID_CONFIG = "Invalid configuration"
    ERROR_TASK_FAILED = "Task failed. Check logs for details"
    
    # Success
    SUCCESS_CONFIG_SAVED = "Configuration saved successfully"
    SUCCESS_TASK_CREATED = "Task created successfully"
    SUCCESS_SCRIPT_GENERATED = "Script generated successfully"
    
    # Info
    INFO_USING_CACHE = "Using cached results"
    INFO_PROCESSING = "Processing..."
    INFO_GENERATING = "Generating..."
    
    # Warnings
    WARN_NO_API_KEY = "No API key configured. Please configure in settings"
    WARN_RATE_LIMIT = "Rate limit exceeded. Please wait"


class VideoProviders:
    """Video stock providers"""
    PEXELS = "pexels"
    PIXABAY = "pixabay"
    LOCAL = "local"
    
    ALL = [PEXELS, PIXABAY, LOCAL]


class LLMProviders:
    """LLM provider names"""
    OPENAI = "OpenAI"
    MOONSHOT = "Moonshot"
    AZURE = "Azure"
    GEMINI = "Gemini"
    ONEAPI = "OneAPI"
    QIANFAN = "Qianfan"
    DEEPSEEK = "DeepSeek"
    CLOUDFLARE = "Cloudflare"
    CHATANYWHERE = "ChatAnyWhere"
    
    ALL = [OPENAI, MOONSHOT, AZURE, GEMINI, ONEAPI, QIANFAN, DEEPSEEK, CLOUDFLARE, CHATANYWHERE]


class VoiceProviders:
    """Voice/TTS providers"""
    EDGE = "edge"
    AZURE = "azure"
    OPENAI = "openai"
    GOOGLE = "g-cloud"
    FISH_AUDIO = "fish-audio"
    CUSTOM = "custom"
    
    ALL = [EDGE, AZURE, OPENAI, GOOGLE, FISH_AUDIO, CUSTOM]


class VideoAspects:
    """Video aspect ratios"""
    PORTRAIT = "9:16"
    LANDSCAPE = "16:9"
    SQUARE = "1:1"
    
    ALL = [PORTRAIT, LANDSCAPE, SQUARE]


class ConcatModes:
    """Video concatenation modes"""
    RANDOM = "random"
    SEQUENTIAL = "sequential"
    
    ALL = [RANDOM, SEQUENTIAL]


class TransitionModes:
    """Video transition effects"""
    NONE = "none"
    FADE_IN = "fade_in"
    FADE_OUT = "fade_out"
    SLIDE_IN = "slide_in"
    SLIDE_OUT = "slide_out"
    SHUFFLE = "shuffle"
    
    ALL = [NONE, FADE_IN, FADE_OUT, SLIDE_IN, SLIDE_OUT, SHUFFLE]


# API rate limiting
MAX_API_CALLS_PER_MINUTE = 30
MAX_SCRIPT_GENERATIONS_PER_HOUR = 100

# File upload limits
MAX_UPLOAD_SIZE_MB = 100
ALLOWED_VIDEO_EXTENSIONS = [".mp4", ".mov", ".avi", ".mkv"]
ALLOWED_AUDIO_EXTENSIONS = [".mp3", ".wav", ".aac", ".m4a"]

# UI performance
CACHE_TTL_SECONDS = 3600  # 1 hour
DEBOUNCE_DELAY_MS = 500
