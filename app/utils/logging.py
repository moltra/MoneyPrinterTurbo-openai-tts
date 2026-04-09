"""
Logging utilities for secure log handling
"""
from typing import Any, Dict, List, Union


def sanitize_log_data(data: Any, sensitive_keys: List[str] = None) -> Any:
    """
    Remove sensitive fields from data before logging
    
    Args:
        data: Data to sanitize (dict, list, or primitive)
        sensitive_keys: List of sensitive key patterns to redact
        
    Returns:
        Sanitized copy of data with sensitive fields redacted
    """
    if sensitive_keys is None:
        sensitive_keys = [
            'api_key', 'apikey', 'api-key',
            'token', 'access_token', 'refresh_token',
            'password', 'passwd', 'pwd',
            'secret', 'private_key', 'privatekey',
            'authorization', 'auth',
            'credential', 'credentials'
        ]
    
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            key_lower = str(key).lower()
            if any(sensitive in key_lower for sensitive in sensitive_keys):
                sanitized[key] = '***REDACTED***'
            elif isinstance(value, (dict, list)):
                sanitized[key] = sanitize_log_data(value, sensitive_keys)
            else:
                sanitized[key] = value
        return sanitized
    
    elif isinstance(data, list):
        return [sanitize_log_data(item, sensitive_keys) for item in data]
    
    elif isinstance(data, tuple):
        return tuple(sanitize_log_data(item, sensitive_keys) for item in data)
    
    else:
        return data


def sanitize_url(url: str) -> str:
    """
    Sanitize URL to hide query parameters that may contain sensitive data
    
    Args:
        url: URL string to sanitize
        
    Returns:
        Sanitized URL with query parameters redacted if they contain sensitive info
    """
    if not url or '?' not in url:
        return url
    
    base_url, query_string = url.split('?', 1)
    
    sensitive_params = ['key', 'token', 'apikey', 'api_key', 'auth', 'secret']
    
    if any(param in query_string.lower() for param in sensitive_params):
        return f"{base_url}?***REDACTED***"
    
    return url
