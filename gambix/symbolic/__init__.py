"""
gambix.symbolic — deterministic tactical/positional detectors.

Public API
----------
detect_check   : check / double-check / checkmate detector
CheckEvidence  : evidence model returned by detect_check
"""

from __future__ import annotations

from gambix.symbolic.check_detector import detect_check
from gambix.symbolic._types import CheckEvidence

__all__ = [
    "detect_check",
    "CheckEvidence",
]
