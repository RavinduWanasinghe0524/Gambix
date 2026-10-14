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


class PinEvidence(BaseModel):
    """Evidence produced by the pin detector for a single pinned piece."""

    model_config = {"frozen": True}

    #: The side whose piece is pinned.
    pinned_side: Literal["white", "black"]

    #: UCI square of the pinned piece.
    pinned_square: str

    #: UCI square of the pinning piece.
    pinner_square: str

    #: UCI square of the piece being shielded (always the king).
    shielded_square: str

    #: Absolute pin: moving the piece would expose the king to check.
    is_absolute: bool


class ForkEvidence(BaseModel):
    """Evidence produced by the fork detector for a single forking piece."""

    model_config = {"frozen": True}

    #: The side delivering the fork.
    forking_side: Literal["white", "black"]

    #: UCI square of the piece delivering the fork.
    forking_square: str

    #: UCI squares of the pieces being attacked simultaneously (≥2).
    forked_squares: list[str] = Field(min_length=2)

    #: True if one of the forked pieces is a king.
    attacks_king: bool


class HangingPieceEvidence(BaseModel):
    """Evidence produced by the hanging-piece detector for one hanging piece."""

    model_config = {"frozen": True}

    #: The side whose piece is hanging.
    hanging_side: Literal["white", "black"]

    #: UCI square of the hanging piece.
    hanging_square: str

    #: Material value of the hanging piece in centipawns.
    piece_value_cp: int

    #: Number of attackers vs defenders (attackers > defenders, or defender count = 0).
    attacker_count: int
    defender_count: int
