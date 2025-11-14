"""
<<<<<<< HEAD
Utility functions for SOBUB AI.
=======
Utility functions for Sobub AI.
>>>>>>> 8a38096837c66815ff3d73c6d5cda79c89c6b57a

This module contains reusable utility functions to eliminate code duplication
and follow the DRY (Don't Repeat Yourself) principle.
"""
import re
from typing import List, Optional
from pathlib import Path

from .config import ValidationRules, StorageConfig
from .logging_config import get_logger

logger = get_logger(__name__)


# ============================================================================
# Tag Processing Utilities
# ============================================================================

def parse_tags(tags_string: str) -> List[str]:
    """
    Parse comma-separated tags into a list.

    This function:
    - Splits on commas
    - Strips whitespace from each tag
    - Removes empty tags
    - Removes duplicates (case-insensitive)
    - Sorts alphabetically

    Args:
        tags_string: Comma-separated string of tags

    Returns:
        List of cleaned, unique tags

    Examples:
        >>> parse_tags("football, goal, sports")
        ['football', 'goal', 'sports']

        >>> parse_tags("  tag1,tag2  , tag1, TAG1,  ")
        ['tag1', 'tag2']
    """
    if not tags_string:
        return []

    # Split and clean
    tags = [tag.strip() for tag in tags_string.split(",") if tag.strip()]

    # Remove duplicates (case-insensitive) while preserving order
    seen = set()
    unique_tags = []
    for tag in tags:
        tag_lower = tag.lower()
        if tag_lower not in seen:
            seen.add(tag_lower)
            unique_tags.append(tag)

    return unique_tags


def validate_tags(tags: List[str]) -> tuple[bool, Optional[str]]:
    """
    Validate a list of tags against validation rules.

    Args:
        tags: List of tags to validate

    Returns:
        Tuple of (is_valid, error_message)

    Examples:
        >>> validate_tags(["football", "goal"])
        (True, None)

        >>> validate_tags([])
        (False, "At least one tag is required")

        >>> validate_tags(["a" * 51])
        (False, "Tag too long: maximum 50 characters")
    """
    if not tags:
        return False, "At least one tag is required"

    if len(tags) > ValidationRules.MAX_TAGS_PER_MEME:
        return False, f"Too many tags: maximum {ValidationRules.MAX_TAGS_PER_MEME} tags allowed"

    for tag in tags:
        if len(tag) < ValidationRules.MIN_TAG_LENGTH:
            return False, f"Tag too short: minimum {ValidationRules.MIN_TAG_LENGTH} character"

        if len(tag) > ValidationRules.MAX_TAG_LENGTH:
            return False, f"Tag too long: maximum {ValidationRules.MAX_TAG_LENGTH} characters"

    return True, None


def sanitize_tag(tag: str) -> str:
    """
    Sanitize a single tag by removing unsafe characters.

    Args:
        tag: Tag string to sanitize

    Returns:
        Sanitized tag string

    Examples:
        >>> sanitize_tag("hello<script>")
        'helloscript'

        >>> sanitize_tag("tag@#$%123")
        'tag123'
    """
    # Remove any non-alphanumeric characters except spaces and hyphens
    sanitized = re.sub(r'[^\w\s\-]', '', tag, flags=re.UNICODE)
    return sanitized.strip()


# ============================================================================
# Filename Utilities
# ============================================================================

def sanitize_filename(filename: str, ensure_extension: str = None) -> str:
    """
    Sanitize a filename to prevent directory traversal and other issues.

    Args:
        filename: Original filename
        ensure_extension: If provided, ensure filename ends with this extension

    Returns:
        Sanitized filename

    Examples:
        >>> sanitize_filename("../../etc/passwd")
        'etcpasswd'

        >>> sanitize_filename("my file.mp3")
        'my_file.mp3'

        >>> sanitize_filename("audio", ensure_extension=".mp3")
        'audio.mp3'
    """
    # Remove path components
    filename = Path(filename).name

    # Replace unsafe characters with underscores
    filename = re.sub(StorageConfig.UNSAFE_FILENAME_CHARS, '_', filename)

    # Remove multiple consecutive underscores
    filename = re.sub(r'_+', '_', filename)

    # Limit length
    if len(filename) > StorageConfig.MAX_FILENAME_LENGTH:
        # Preserve extension if present
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        max_name_len = StorageConfig.MAX_FILENAME_LENGTH - len(ext) - 1
        filename = f"{name[:max_name_len]}.{ext}" if ext else name[:StorageConfig.MAX_FILENAME_LENGTH]

    # Ensure extension if requested
    if ensure_extension and not filename.endswith(ensure_extension):
        filename = f"{filename}{ensure_extension}"

    return filename


def is_allowed_file_extension(filename: str, allowed_extensions: set = None) -> bool:
    """
    Check if a filename has an allowed extension.

    Args:
        filename: Filename to check
        allowed_extensions: Set of allowed extensions (defaults to audio extensions)

    Returns:
        True if extension is allowed, False otherwise

    Examples:
        >>> is_allowed_file_extension("audio.mp3")
        True

        >>> is_allowed_file_extension("video.mp4")
        False
    """
    allowed = allowed_extensions or StorageConfig.ALLOWED_AUDIO_EXTENSIONS
    ext = Path(filename).suffix.lower()
    return ext in allowed


# ============================================================================
# String Utilities
# ============================================================================

def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum length, adding a suffix if truncated.

    Args:
        text: String to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated string

    Examples:
        >>> truncate_string("Hello World", 8)
        'Hello...'

        >>> truncate_string("Short", 10)
        'Short'
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in a string (replace multiple spaces with single space).

    Args:
        text: String to normalize

    Returns:
        Normalized string

    Examples:
        >>> normalize_whitespace("hello    world")
        'hello world'

        >>> normalize_whitespace("  trim  me  ")
        'trim me'
    """
    return ' '.join(text.split())


# ============================================================================
# Validation Utilities
# ============================================================================

def is_valid_probability(value: float) -> bool:
    """
    Check if a value is a valid probability (0-100).

    Args:
        value: Value to check

    Returns:
        True if valid, False otherwise

    Examples:
        >>> is_valid_probability(50.0)
        True

        >>> is_valid_probability(150.0)
        False
    """
    return ValidationRules.MIN_TRIGGER_PROBABILITY <= value <= ValidationRules.MAX_TRIGGER_PROBABILITY


def is_valid_cooldown(value: int) -> bool:
    """
    Check if a value is a valid cooldown duration in seconds.

    Args:
        value: Value to check in seconds

    Returns:
        True if valid, False otherwise

    Examples:
        >>> is_valid_cooldown(180)
        True

        >>> is_valid_cooldown(-1)
        False
    """
    return ValidationRules.MIN_COOLDOWN_SECONDS <= value <= ValidationRules.MAX_COOLDOWN_SECONDS


def clamp(value: float, min_value: float, max_value: float) -> float:
    """
    Clamp a value between min and max.

    Args:
        value: Value to clamp
        min_value: Minimum value
        max_value: Maximum value

    Returns:
        Clamped value

    Examples:
        >>> clamp(50, 0, 100)
        50

        >>> clamp(150, 0, 100)
        100

        >>> clamp(-10, 0, 100)
        0
    """
    return max(min_value, min(value, max_value))
