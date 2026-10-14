"""
gambix.symbolic — deterministic tactical/positional detectors.

Public API
----------
detect_check          : check / double-check / checkmate detector
detect_pins           : absolute pin detector (both sides)
detect_forks          : fork detector (both sides)
detect_hanging_pieces : hanging piece detector (both sides)

Evidence models
---------------
CheckEvidence
PinEvidence
ForkEvidence
HangingPieceEvidence
"""

from __future__ import annotations

from gambix.symbolic._types import (
    CheckEvidence,
    ForkEvidence,
    HangingPieceEvidence,
    PinEvidence,
)
from gambix.symbolic.check_detector import detect_check
from gambix.symbolic.fork_detector import detect_forks
from gambix.symbolic.hanging_detector import detect_hanging_pieces
from gambix.symbolic.pin_detector import detect_pins

__all__ = [
    # Detectors
    "detect_check",
    "detect_pins",
    "detect_forks",
    "detect_hanging_pieces",
    # Evidence models
    "CheckEvidence",
    "PinEvidence",
    "ForkEvidence",
    "HangingPieceEvidence",
]
