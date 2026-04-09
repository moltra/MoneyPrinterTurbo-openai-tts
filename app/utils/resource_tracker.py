"""
Resource tracking and cleanup utility for video processing tasks
"""
from typing import Any, List
from loguru import logger


class ResourceTracker:
    """
    Tracks resources (video clips, audio clips, file handles) for cleanup
    """
    
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.resources: List[Any] = []
        
    def track(self, resource: Any) -> Any:
        """
        Track a resource for later cleanup
        
        Args:
            resource: Resource to track (clip, file handle, etc.)
            
        Returns:
            The resource itself (for chaining)
        """
        if resource is not None:
            self.resources.append(resource)
        return resource
    
    def cleanup(self):
        """
        Clean up all tracked resources
        """
        cleanup_errors = []
        
        for resource in reversed(self.resources):
            try:
                # Try common cleanup methods
                if hasattr(resource, 'close'):
                    resource.close()
                elif hasattr(resource, 'reader') and hasattr(resource.reader, 'close'):
                    resource.reader.close()
                    
                # Clean up audio if present
                if hasattr(resource, 'audio') and resource.audio is not None:
                    if hasattr(resource.audio, 'reader') and resource.audio.reader is not None:
                        resource.audio.reader.close()
                    if hasattr(resource.audio, 'close'):
                        resource.audio.close()
                        
            except Exception as e:
                cleanup_errors.append(str(e))
                
        self.resources.clear()
        
        if cleanup_errors:
            logger.warning(f"Task {self.task_id}: Resource cleanup had {len(cleanup_errors)} errors (non-fatal)")
            
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
        return False
