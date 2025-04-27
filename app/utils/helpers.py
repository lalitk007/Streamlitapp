# app/utils/helpers.py
import re
from typing import List, Dict, Any
from urllib.parse import urlparse
import time


def format_time(seconds: float) -> str:
    """
    Format time in seconds to a human-readable string
    """
    if seconds < 0.001:
        return f"{seconds * 1000000:.2f} μs"
    elif seconds < 1:
        return f"{seconds * 1000:.2f} ms"
    else:
        return f"{seconds:.2f} s"


def extract_domain(url: str) -> str:
    """
    Extract the domain from a URL
    """
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        return domain
    except:
        return ""


def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to a maximum length
    """
    if not text:
        return ""

    if len(text) <= max_length:
        return text

    return text[:max_length] + "..."


def highlight_terms(text: str, terms: List[str]) -> str:
    """
    Highlight search terms in text
    """
    if not text or not terms:
        return text

    highlighted = text
    for term in terms:
        if len(term) < 3:  # Skip very short terms
            continue

        pattern = re.compile(re.escape(term), re.IGNORECASE)
        highlighted = pattern.sub(f"<mark>{term}</mark>", highlighted)

    return highlighted


def get_timestamp() -> str:
    """
    Get current timestamp in a readable format
    """
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())