"""
Video file validation utilities
"""
import os
from loguru import logger
from moviepy import VideoFileClip


def validate_video_file(video_path: str, min_duration: float = 0.1) -> bool:
    """
    Validate that a video file is not corrupted and has valid properties
    
    Args:
        video_path: Path to video file
        min_duration: Minimum duration in seconds (default 0.1)
        
    Returns:
        True if video is valid, False otherwise
    """
    if not os.path.exists(video_path):
        logger.warning(f"Video file does not exist: {video_path}")
        return False
    
    if os.path.getsize(video_path) == 0:
        logger.warning(f"Video file is empty: {video_path}")
        return False
    
    try:
        clip = VideoFileClip(video_path)
        duration = clip.duration
        fps = clip.fps
        width, height = clip.size
        
        # Close clip immediately to free resources
        clip.close()
        del clip
        
        # Validate metrics
        if duration <= 0 or duration < min_duration:
            logger.warning(f"Invalid video duration {duration}s: {video_path}")
            return False
            
        if fps <= 0:
            logger.warning(f"Invalid video fps {fps}: {video_path}")
            return False
        
        if width <= 0 or height <= 0:
            logger.warning(f"Invalid video dimensions {width}x{height}: {video_path}")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Video validation failed for {video_path}: {str(e)}")
        return False


def validate_video_quality(
    video_path: str,
    min_resolution: tuple = (720, 480),
    min_fps: float = 20.0
) -> bool:
    """
    Validate video meets minimum quality standards
    
    Args:
        video_path: Path to video file
        min_resolution: Minimum (width, height) tuple
        min_fps: Minimum frames per second
        
    Returns:
        True if video meets quality standards
    """
    if not validate_video_file(video_path):
        return False
    
    try:
        clip = VideoFileClip(video_path)
        width, height = clip.size
        fps = clip.fps
        clip.close()
        del clip
        
        if width < min_resolution[0] or height < min_resolution[1]:
            logger.warning(
                f"Video resolution {width}x{height} below minimum {min_resolution}: {video_path}"
            )
            return False
        
        if fps < min_fps:
            logger.warning(f"Video fps {fps} below minimum {min_fps}: {video_path}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Video quality check failed for {video_path}: {str(e)}")
        return False
