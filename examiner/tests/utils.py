"""Module for examiner test utilities."""

import hashlib


def sha1(text: str) -> str:
    """Return SHA1 hexadecimal of string."""
    return hashlib.sha1(text).hexdigest()
