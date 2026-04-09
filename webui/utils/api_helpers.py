"""
API Helper Functions
Wrappers for API calls with error handling and user feedback
"""
import time
from typing import Any, Callable, Optional, List
from functools import wraps
import streamlit as st
from loguru import logger
import requests

from webui.utils.constants import UIMessages, MAX_API_CALLS_PER_MINUTE
from webui.utils.session_state import get_state


def safe_api_call(
    func: Callable,
    *args,
    error_msg: str = "Operation failed",
    show_spinner: bool = True,
    spinner_text: str = "Processing...",
    **kwargs
) -> Optional[Any]:
    """
    Wrapper for API calls with user feedback and error handling
    
    Args:
        func: Function to call
        *args: Positional arguments for function
        error_msg: Error message to show user
        show_spinner: Whether to show spinner during call
        spinner_text: Text to show in spinner
        **kwargs: Keyword arguments for function
        
    Returns:
        Function result or None on error
    """
    try:
        if show_spinner:
            with st.spinner(spinner_text):
                result = func(*args, **kwargs)
        else:
            result = func(*args, **kwargs)
        
        # Check for string-based errors (legacy pattern)
        if isinstance(result, str) and result.startswith("Error: "):
            st.error(f"{error_msg}: {result[7:]}")
            return None
        
        return result
        
    except requests.RequestException as e:
        st.error(f"{error_msg}: {UIMessages.ERROR_NETWORK}")
        logger.exception(f"Network error in {func.__name__}: {e}")
        return None
        
    except ValueError as e:
        st.error(f"{error_msg}: Invalid input - {str(e)}")
        logger.exception(f"Validation error in {func.__name__}: {e}")
        return None
        
    except Exception as e:
        st.error(f"{error_msg}: {str(e)}")
        logger.exception(f"Unexpected error in {func.__name__}: {e}")
        return None


def rate_limit(calls_per_minute: int = MAX_API_CALLS_PER_MINUTE):
    """
    Decorator to rate limit function calls
    
    Args:
        calls_per_minute: Maximum calls allowed per minute
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            state = get_state()
            now = time.time()
            
            # Remove calls older than 1 minute
            state.last_api_calls = [
                t for t in state.last_api_calls 
                if now - t < 60
            ]
            
            # Check if rate limit exceeded
            if len(state.last_api_calls) >= calls_per_minute:
                st.error(UIMessages.WARN_RATE_LIMIT)
                st.stop()
            
            # Record this call
            state.last_api_calls.append(now)
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def with_progress(
    items: List[Any],
    process_func: Callable,
    status_text_template: str = "Processing {current}/{total}: {item}",
    error_handler: Optional[Callable] = None
) -> tuple[List[Any], List[dict]]:
    """
    Process items with progress bar and status updates
    
    Args:
        items: List of items to process
        process_func: Function to process each item
        status_text_template: Template for status text (supports {current}, {total}, {item})
        error_handler: Optional function to handle errors (receives item and exception)
        
    Returns:
        Tuple of (successful_results, failed_items_with_errors)
    """
    if not items:
        return [], []
    
    progress_bar = st.progress(0)
    status_container = st.empty()
    
    successful = []
    failed = []
    
    for i, item in enumerate(items):
        # Update progress
        progress = (i + 1) / len(items)
        progress_bar.progress(progress)
        
        # Update status text
        status_text = status_text_template.format(
            current=i + 1,
            total=len(items),
            item=str(item)[:50]  # Truncate long items
        )
        status_container.text(status_text)
        
        try:
            result = process_func(item)
            successful.append(result)
        except Exception as e:
            logger.error(f"Error processing item {i}: {str(e)}")
            
            error_info = {
                "item": item,
                "error": str(e),
                "index": i
            }
            failed.append(error_info)
            
            if error_handler:
                error_handler(item, e)
    
    # Clean up progress indicators
    progress_bar.empty()
    status_container.empty()
    
    return successful, failed


def retry_on_failure(
    max_retries: int = 3,
    delay_seconds: float = 1.0,
    backoff_factor: float = 2.0
):
    """
    Decorator to retry function on failure with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts
        delay_seconds: Initial delay between retries
        backoff_factor: Multiplier for delay on each retry
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay_seconds
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {str(e)}. "
                            f"Retrying in {current_delay}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}")
            
            # All retries exhausted
            raise last_exception
        
        return wrapper
    return decorator


def validate_and_call(
    func: Callable,
    validation_func: Callable,
    *args,
    error_prefix: str = "Validation failed",
    **kwargs
) -> Optional[Any]:
    """
    Validate inputs before calling function
    
    Args:
        func: Function to call
        validation_func: Validation function that returns (is_valid, errors)
        *args: Arguments to pass to validation and main function
        error_prefix: Prefix for error messages
        **kwargs: Keyword arguments to pass to validation and main function
        
    Returns:
        Function result or None if validation fails
    """
    # Run validation
    is_valid, errors = validation_func(*args, **kwargs)
    
    if not is_valid:
        for error in errors:
            st.error(f"{error_prefix}: {error}")
        return None
    
    # Validation passed, call the function
    return func(*args, **kwargs)


def cache_result(cache_key_func: Callable, ttl: int = 3600):
    """
    Decorator to cache function results in session state
    
    Args:
        cache_key_func: Function to generate cache key from arguments
        ttl: Time to live in seconds
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            from webui.utils.session_state import get_from_cache, save_to_cache
            
            # Generate cache key
            cache_key = cache_key_func(*args, **kwargs)
            
            # Check cache
            cached_result = get_from_cache(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}: {cache_key}")
                return cached_result
            
            # Cache miss, call function
            logger.debug(f"Cache miss for {func.__name__}: {cache_key}")
            result = func(*args, **kwargs)
            
            # Save to cache
            save_to_cache(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator
