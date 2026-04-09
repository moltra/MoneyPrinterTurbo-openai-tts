"""
Video processing constants
Centralized location for configuration values to improve maintainability
"""


class VideoConstants:
    """Constants for video processing operations"""
    
    # Clip search and download limits
    DEFAULT_CLIP_SEARCH_LIMIT = 20
    MAX_CLIP_SEARCH_LIMIT = 50
    
    # Video duration constraints (in seconds)
    MIN_CLIP_DURATION_SECONDS = 3
    DEFAULT_MAX_CLIP_DURATION = 5
    
    # Semantic scoring
    SEMANTIC_TOP_K_CLIPS = 6
    MAX_SENTENCE_TERMS = 30
    
    # Cache settings
    CACHE_TTL_DAYS = 7
    
    # Video quality thresholds
    MIN_VIDEO_RESOLUTION_WIDTH = 720
    MIN_VIDEO_RESOLUTION_HEIGHT = 480
    MIN_VIDEO_FPS = 20.0
    
    # Clip failure tolerance (percentage)
    MAX_CLIP_FAILURE_RATIO = 0.3  # 30% of clips can fail before task fails
    
    # Download and processing
    DEFAULT_VIDEO_ORIENTATION = "portrait"
    DEFAULT_THREADS = 2
    DEFAULT_FPS = 30
    
    # Audio
    DEFAULT_AUDIO_CODEC = "aac"
    
    # Timeouts (in seconds)
    API_REQUEST_TIMEOUT_CONNECT = 30
    API_REQUEST_TIMEOUT_READ = 60
    VIDEO_DOWNLOAD_TIMEOUT_CONNECT = 60
    VIDEO_DOWNLOAD_TIMEOUT_READ = 240


class APIConstants:
    """Constants for external API integrations"""
    
    # Pexels API
    PEXELS_DEFAULT_PER_PAGE = 20
    PEXELS_MAX_PER_PAGE = 80
    
    # Pixabay API
    PIXABAY_DEFAULT_PER_PAGE = 20
    PIXABAY_MAX_PER_PAGE = 200
    
    # Rate limiting (requests per hour for free tier)
    PEXELS_FREE_TIER_LIMIT = 200
    PIXABAY_FREE_TIER_LIMIT = 5000


class SemanticConstants:
    """Constants for semantic scoring and search"""
    
    # Number of search queries to generate per sentence
    DEFAULT_QUERIES_PER_SENTENCE = 3
    MAX_QUERIES_PER_SENTENCE = 5
    
    # Top-k clips to select after semantic scoring
    DEFAULT_TOP_K = 6
    MAX_TOP_K = 10
    
    # Minimum semantic similarity score (0.0 to 1.0)
    MIN_SIMILARITY_SCORE = 0.3
