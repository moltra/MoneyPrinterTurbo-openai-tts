"""
Ollama API Helper Functions
Utilities for fetching available models from Ollama server
"""
import requests
from typing import List, Optional, Tuple
from loguru import logger


def fetch_ollama_models(base_url: str, timeout: int = 5) -> Tuple[bool, List[str], Optional[str]]:
    """
    Fetch available models from Ollama API
    
    Args:
        base_url: Ollama base URL (e.g., http://localhost:11434/v1 or http://localhost:11434)
        timeout: Request timeout in seconds
        
    Returns:
        Tuple of (success, model_list, error_message)
    """
    if not base_url:
        return False, [], "Base URL is empty"
    
    # Clean up the base URL - Ollama API is at /api/tags, not /v1/api/tags
    base_url = base_url.rstrip("/")
    if base_url.endswith("/v1"):
        base_url = base_url[:-3]  # Remove /v1 suffix
    
    api_url = f"{base_url}/api/tags"
    
    try:
        logger.debug(f"Fetching Ollama models from: {api_url}")
        response = requests.get(api_url, timeout=timeout)
        response.raise_for_status()
        
        data = response.json()
        models = data.get("models", [])
        
        if not models:
            return True, [], "No models found on Ollama server"
        
        # Extract model names
        model_names = []
        for model in models:
            if isinstance(model, dict):
                name = model.get("name", "")
            else:
                name = str(model)
            
            if name:
                model_names.append(name)
        
        logger.success(f"Found {len(model_names)} Ollama models")
        return True, sorted(model_names), None
        
    except requests.exceptions.ConnectionError:
        error_msg = f"Cannot connect to Ollama at {base_url}"
        logger.warning(error_msg)
        return False, [], error_msg
        
    except requests.exceptions.Timeout:
        error_msg = f"Ollama API request timed out after {timeout}s"
        logger.warning(error_msg)
        return False, [], error_msg
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Ollama API error: {str(e)}"
        logger.error(error_msg)
        return False, [], error_msg
        
    except Exception as e:
        error_msg = f"Unexpected error fetching Ollama models: {str(e)}"
        logger.exception(error_msg)
        return False, [], error_msg


def test_ollama_connection(base_url: str, timeout: int = 5) -> Tuple[bool, Optional[str]]:
    """
    Test connection to Ollama server
    
    Args:
        base_url: Ollama base URL
        timeout: Request timeout in seconds
        
    Returns:
        Tuple of (success, error_message)
    """
    if not base_url:
        return False, "Base URL is empty"
    
    # Clean up the base URL
    base_url = base_url.rstrip("/")
    if base_url.endswith("/v1"):
        base_url = base_url[:-3]
    
    api_url = f"{base_url}/api/tags"
    
    try:
        response = requests.get(api_url, timeout=timeout)
        response.raise_for_status()
        return True, None
    except requests.exceptions.ConnectionError:
        return False, f"Cannot connect to Ollama at {base_url}"
    except requests.exceptions.Timeout:
        return False, f"Connection timed out after {timeout}s"
    except Exception as e:
        return False, str(e)


def get_model_display_name(model_name: str) -> str:
    """
    Format model name for display
    
    Args:
        model_name: Raw model name from Ollama
        
    Returns:
        Formatted display name
    """
    if not model_name:
        return ""
    
    # Example: "llama2:7b" -> "Llama2 (7B)"
    # Example: "qwen:7b" -> "Qwen (7B)"
    parts = model_name.split(":")
    if len(parts) == 2:
        base_name = parts[0].title()
        variant = parts[1].upper()
        return f"{base_name} ({variant})"
    
    return model_name


def get_ollama_model_info(base_url: str, model_name: str, timeout: int = 5) -> Optional[dict]:
    """
    Get detailed information about a specific Ollama model
    
    Args:
        base_url: Ollama base URL
        model_name: Name of the model
        timeout: Request timeout in seconds
        
    Returns:
        Model info dict or None if error
    """
    if not base_url or not model_name:
        return None
    
    # Clean up the base URL
    base_url = base_url.rstrip("/")
    if base_url.endswith("/v1"):
        base_url = base_url[:-3]
    
    api_url = f"{base_url}/api/show"
    
    try:
        response = requests.post(
            api_url,
            json={"name": model_name},
            timeout=timeout
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.warning(f"Failed to get info for model {model_name}: {e}")
        return None
