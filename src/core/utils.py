"""Shared utility functions for core domain."""

import html
import re
from datetime import UTC, datetime
from typing import Annotated

from pydantic import BeforeValidator

# Regex for PII detection
_EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
# Phone pattern: international or local formats
_PHONE_PATTERN = re.compile(r"\+?\d[\d\s\-().]{7,}\d")


def utcnow() -> datetime:
    """Return timezone-aware UTC now (replacement for deprecated datetime.utcnow)."""
    return datetime.now(UTC)


def sanitize_html(value: str) -> str:
    """Strip HTML tags and escape special chars to prevent XSS."""
    return html.escape(value, quote=True) if value else value


def mask_pii(text: str, mask: str = "***") -> str:
    """Mask PII (emails, phone numbers) in a string for safe logging.

    Args:
        text: The input string that may contain PII.
        mask: Replacement token (default ``***``).

    Returns:
        String with PII replaced by the mask token.
    """
    result = _EMAIL_PATTERN.sub(mask, text)
    return _PHONE_PATTERN.sub(mask, result)


# Convenience type for PII-safe, XSS-sanitized string fields
SanitizedStr = Annotated[str, BeforeValidator(sanitize_html)]
