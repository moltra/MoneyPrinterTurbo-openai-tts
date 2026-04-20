"""
Performance Profiling Utilities using PyInstrument
Provides decorators and context managers for profiling functions and API calls
"""
import os
import functools
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable, Any
from loguru import logger
from pyinstrument import Profiler


# Profiling configuration
PROFILING_ENABLED = os.getenv("ENABLE_PROFILING", "false").lower() == "true"
PROFILE_OUTPUT_DIR = os.getenv("PROFILE_OUTPUT_DIR", "/MoneyPrinterTurbo/storage/profiles")
PROFILE_MIN_DURATION = float(os.getenv("PROFILE_MIN_DURATION", "0.1"))  # Only log if > 100ms


def ensure_profile_dir():
    """Ensure profile output directory exists"""
    Path(PROFILE_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)


def profile_function(
    name: Optional[str] = None,
    save_html: bool = False,
    print_results: bool = True,
    min_duration: Optional[float] = None
):
    """
    Decorator to profile a function's performance
    
    Usage:
        @profile_function(name="video_processing", save_html=True)
        def process_video(task_id: str):
            # ... code ...
            pass
    
    Args:
        name: Custom name for the profile (defaults to function name)
        save_html: Save HTML report to disk
        print_results: Print results to logger
        min_duration: Only log if execution time > this (seconds)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if not PROFILING_ENABLED:
                # Profiling disabled, just run function
                return func(*args, **kwargs)
            
            profile_name = name or func.__name__
            profiler = Profiler()
            
            try:
                profiler.start()
                result = func(*args, **kwargs)
                profiler.stop()
                
                # Get duration
                duration = profiler.last_session.duration
                
                # Check minimum duration threshold
                threshold = min_duration if min_duration is not None else PROFILE_MIN_DURATION
                if duration < threshold:
                    return result
                
                # Log results
                if print_results:
                    logger.info(f"⏱️  Profile: {profile_name} took {duration:.3f}s")
                    logger.debug(f"\n{profiler.output_text(unicode=True, color=True)}")
                
                # Save HTML report
                if save_html:
                    ensure_profile_dir()
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{profile_name}_{timestamp}.html"
                    filepath = Path(PROFILE_OUTPUT_DIR) / filename
                    
                    with open(filepath, 'w') as f:
                        f.write(profiler.output_html())
                    
                    logger.info(f"📊 Profile saved: {filepath}")
                
                return result
            
            except Exception as e:
                profiler.stop()
                logger.error(f"Profiling error in {profile_name}: {e}")
                raise
        
        return wrapper
    return decorator


class ProfileContext:
    """
    Context manager for profiling code blocks
    
    Usage:
        with ProfileContext("api_call") as p:
            response = requests.get(url)
            data = response.json()
        
        # Access results
        print(f"Duration: {p.duration}s")
    """
    
    def __init__(
        self,
        name: str,
        save_html: bool = False,
        print_results: bool = True,
        min_duration: Optional[float] = None
    ):
        self.name = name
        self.save_html = save_html
        self.print_results = print_results
        self.min_duration = min_duration if min_duration is not None else PROFILE_MIN_DURATION
        self.profiler = Profiler()
        self.duration = 0.0
        self.enabled = PROFILING_ENABLED
    
    def __enter__(self):
        if self.enabled:
            self.profiler.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.enabled:
            return False
        
        self.profiler.stop()
        self.duration = self.profiler.last_session.duration
        
        # Check minimum duration
        if self.duration < self.min_duration:
            return False
        
        # Log results
        if self.print_results:
            logger.info(f"⏱️  Profile: {self.name} took {self.duration:.3f}s")
            logger.debug(f"\n{self.profiler.output_text(unicode=True, color=True)}")
        
        # Save HTML report
        if self.save_html:
            ensure_profile_dir()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.name}_{timestamp}.html"
            filepath = Path(PROFILE_OUTPUT_DIR) / filename
            
            with open(filepath, 'w') as f:
                f.write(self.profiler.output_html())
            
            logger.info(f"📊 Profile saved: {filepath}")
        
        return False


def profile_api_endpoint(name: Optional[str] = None, save_html: bool = False):
    """
    Decorator specifically for FastAPI endpoints
    
    Usage:
        @router.post("/api/v1/videos")
        @profile_api_endpoint(name="create_video", save_html=True)
        async def create_video(params: VideoParams):
            # ... code ...
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            if not PROFILING_ENABLED:
                return await func(*args, **kwargs)
            
            profile_name = name or f"api_{func.__name__}"
            profiler = Profiler()
            
            try:
                profiler.start()
                result = await func(*args, **kwargs)
                profiler.stop()
                
                duration = profiler.last_session.duration
                
                if duration >= PROFILE_MIN_DURATION:
                    logger.info(f"⏱️  API Profile: {profile_name} took {duration:.3f}s")
                    logger.debug(f"\n{profiler.output_text(unicode=True, color=True)}")
                    
                    if save_html:
                        ensure_profile_dir()
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"{profile_name}_{timestamp}.html"
                        filepath = Path(PROFILE_OUTPUT_DIR) / filename
                        
                        with open(filepath, 'w') as f:
                            f.write(profiler.output_html())
                        
                        logger.info(f"📊 API Profile saved: {filepath}")
                
                return result
            
            except Exception as e:
                profiler.stop()
                logger.error(f"API Profiling error in {profile_name}: {e}")
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            if not PROFILING_ENABLED:
                return func(*args, **kwargs)
            
            profile_name = name or f"api_{func.__name__}"
            profiler = Profiler()
            
            try:
                profiler.start()
                result = func(*args, **kwargs)
                profiler.stop()
                
                duration = profiler.last_session.duration
                
                if duration >= PROFILE_MIN_DURATION:
                    logger.info(f"⏱️  API Profile: {profile_name} took {duration:.3f}s")
                    logger.debug(f"\n{profiler.output_text(unicode=True, color=True)}")
                    
                    if save_html:
                        ensure_profile_dir()
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"{profile_name}_{timestamp}.html"
                        filepath = Path(PROFILE_OUTPUT_DIR) / filename
                        
                        with open(filepath, 'w') as f:
                            f.write(profiler.output_html())
                        
                        logger.info(f"📊 API Profile saved: {filepath}")
                
                return result
            
            except Exception as e:
                profiler.stop()
                logger.error(f"API Profiling error in {profile_name}: {e}")
                raise
        
        # Return async or sync wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Convenience functions for quick profiling
def start_profile(name: str = "session") -> Profiler:
    """
    Start a profiler session
    
    Usage:
        profiler = start_profile("video_gen")
        # ... code ...
        stop_profile(profiler, "video_gen")
    """
    profiler = Profiler()
    profiler.start()
    logger.debug(f"▶️  Started profiling: {name}")
    return profiler


def stop_profile(
    profiler: Profiler,
    name: str = "session",
    save_html: bool = False,
    print_results: bool = True
):
    """
    Stop profiler and optionally save results
    
    Args:
        profiler: Profiler instance from start_profile()
        name: Name for the profile
        save_html: Save HTML report
        print_results: Print to logger
    """
    profiler.stop()
    duration = profiler.last_session.duration
    
    logger.info(f"⏹️  Stopped profiling: {name} ({duration:.3f}s)")
    
    if print_results:
        logger.info(f"\n{profiler.output_text(unicode=True, color=True)}")
    
    if save_html:
        ensure_profile_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.html"
        filepath = Path(PROFILE_OUTPUT_DIR) / filename
        
        with open(filepath, 'w') as f:
            f.write(profiler.output_html())
        
        logger.info(f"📊 Profile saved: {filepath}")
