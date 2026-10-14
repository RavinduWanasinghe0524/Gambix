"""
Shared types for the symbolic detector layer.

All detectors return an ``Evidence`` object so the pipeline can merge
results uniformly regardless of which detector produced them.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class CheckEvidence(BaseModel):
    """Evidence produced by the check detector."""

    model_config = {"frozen": True}

    #: The side that is in check.
    side_in_check: Literal["white", "black"]

    #: UCI squares of the checking pieces (e.g. ["e5", "h5"]).
    checking_pieces: list[str] = Field(min_length=1)

    #: True when more than one piece delivers check simultaneously.
    is_double_check: bool

    #: True when the king has no legal escape (checkmate).
    is_checkmate: bool
