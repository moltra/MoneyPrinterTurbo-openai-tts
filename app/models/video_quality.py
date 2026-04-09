"""
Video quality configuration and presets
"""
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class VideoQualityConfig:
    """Video quality configuration"""
    codec: str
    params: List[str]
    bitrate: str
    description: str


VIDEO_QUALITY_PRESETS: Dict[str, VideoQualityConfig] = {
    'low': VideoQualityConfig(
        codec='libx264',
        params=['-preset', 'fast', '-crf', '28'],
        bitrate='1M',
        description='Fast encoding, lower quality (good for previews)'
    ),
    'medium': VideoQualityConfig(
        codec='libx264',
        params=['-preset', 'medium', '-crf', '23'],
        bitrate='2.5M',
        description='Balanced quality and encoding time'
    ),
    'high': VideoQualityConfig(
        codec='libx264',
        params=['-preset', 'slow', '-crf', '18'],
        bitrate='5M',
        description='High quality, slower encoding'
    ),
    'gpu_nvenc': VideoQualityConfig(
        codec='h264_nvenc',
        params=['-preset', 'p4', '-rc', 'vbr', '-cq', '19'],
        bitrate='4M',
        description='Hardware accelerated (NVIDIA GPU required)'
    ),
}


def get_video_quality_config(quality: str = 'medium') -> VideoQualityConfig:
    """
    Get video encoding configuration for specified quality level
    
    Args:
        quality: Quality preset name (low, medium, high, gpu_nvenc)
        
    Returns:
        VideoQualityConfig with encoding parameters
    """
    if quality not in VIDEO_QUALITY_PRESETS:
        from loguru import logger
        logger.warning(f"Unknown video quality '{quality}', using 'medium'")
        quality = 'medium'
    
    return VIDEO_QUALITY_PRESETS[quality]


def list_quality_presets() -> Dict[str, str]:
    """
    List available quality presets with descriptions
    
    Returns:
        Dict mapping quality name to description
    """
    return {
        name: config.description 
        for name, config in VIDEO_QUALITY_PRESETS.items()
    }
