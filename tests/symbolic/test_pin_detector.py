"""
Tests for gambix.symbolic.pin_detector.

Coverage targets
----------------
- No pins           → empty list
- Classic bishop pin (bishop pins knight to king on diagonal)
- Rook pin (rook pins piece to king on file/rank)
- Queen pin
- Both sides can have pins simultaneously
- Blocker between slider and pinned piece → NOT a pin
- Two pieces between slider and king → NOT a pin
- Pinned piece square/pinner square are correct UCI names
- is_absolute is always True
- Property: every pinned_square is a real board square
- Property: detect_pins is consistent — pinned piece is between pinner and king
"""

from __future__ import annotations

import chess
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from gambix.symbolic import PinEvidence, detect_pins


def board_from_fen(fen: str) -> chess.Board:
    return chess.Board(fen)


# ---------------------------------------------------------------------------
# No pin
# ---------------------------------------------------------------------------


class TestNoPin:
    def test_starting_position(self) -> None:
        """No pins in the starting position."""
        assert detect_pins(chess.Board()) == []

    def test_open_position_no_sliders(self) -> None:
        """King vs king — no sliders → no pins."""
        board = board_from_fen("4k3/8/8/8/8/8/8/4K3 w - - 0 1")
        assert detect_pins(board) == []

    def test_blocker_prevents_pin(self) -> None:
        """A second piece between slider and potential victim blocks the pin."""
        # White: King e1, rook a1. Black: King e8, knight d1 (blocks), rook on a8.
        # Black rook a8 → king e8: no pin because nothing is between them on rank.
        # White rook a1 → knight on d1: blocked by another piece means no pin.
        # Use: White king e1, black queen a5; white knight b4 (blocks), white rook b1
        # queen a5 → king e1 diagonal: b4 in between. But another piece on c3 also.
        board = board_from_fen("4k3/8/8/q7/1n6/2P5/8/4K3 w - - 0 1")
        # queen a5 attacks e1 diagonally; b4(knight) AND c3(pawn) are between → not a pin
        assert detect_pins(board) == []

    def test_two_pieces_between_slider_and_king(self) -> None:
        """Two pieces between slider and king — no pin (need exactly one)."""
        # White: king e1, bishop c3, knight d2. Black: queen a5.
        # queen a5 → e1 diagonal: c3 and d2 are both in between → not a pin
        board = board_from_fen("4k3/8/8/q7/8/2B5/3N4/4K3 w - - 0 1")
        assert detect_pins(board) == []


# ---------------------------------------------------------------------------
# Bishop pin
# ---------------------------------------------------------------------------


class TestBishopPin:
    def test_bishop_pins_knight_on_diagonal(self) -> None:
        """Black bishop b4 pins white knight c3 to white king e1."""
        board = board_from_fen("4k3/8/8/8/1b6/2N5/8/4K3 w - - 0 1")
        pins = detect_pins(board)
        assert len(pins) == 1
        p = pins[0]
        assert p.pinned_side == "white"
        assert p.pinned_square == "c3"
        assert p.pinner_square == "b4"
        assert p.shielded_square == "e1"
        assert p.is_absolute is True

    def test_white_bishop_pins_black_piece(self) -> None:
        """White bishop b5 pins black knight c6 to black king e8."""
        board = board_from_fen("4k3/8/2n5/1B6/8/8/8/4K3 b - - 0 1")
        pins = detect_pins(board)
        assert len(pins) == 1
        p = pins[0]
        assert p.pinned_side == "black"
        assert p.pinned_square == "c6"
        assert p.pinner_square == "b5"
        assert p.shielded_square == "e8"


# ---------------------------------------------------------------------------
# Rook pin
# ---------------------------------------------------------------------------


class TestRookPin:
    def test_rook_pin_on_file(self) -> None:
        """White rook e1 pins black bishop e6 to black king e8."""
        board = board_from_fen("4k3/8/4b3/8/8/8/8/4R2K w - - 0 1")
        pins = detect_pins(board)
        assert len(pins) == 1
        p = pins[0]
        assert p.pinned_side == "black"
        assert p.pinned_square == "e6"
        assert p.pinner_square == "e1"
        assert p.shielded_square == "e8"

    def test_rook_pin_on_rank(self) -> None:
        """Black rook a8 pins white rook d8 to white king h8."""
        board = board_from_fen("r2R3K/8/8/8/8/8/8/4k3 w - - 0 1")
        pins = detect_pins(board)
        assert len(pins) == 1
        p = pins[0]
        assert p.pinned_side == "white"
        assert p.pinned_square == "d8"
        assert p.pinner_square == "a8"
        assert p.shielded_square == "h8"


# ---------------------------------------------------------------------------
# Queen pin
# ---------------------------------------------------------------------------


class TestQueenPin:
    def test_queen_pin_on_diagonal(self) -> None:
        """Black queen a1 pins white knight c3 to white king e5."""
        # a1-e5 diagonal: b2, c3, d4 are between. White knight c3 is pinned.
        board = board_from_fen("4k3/8/8/4K3/8/2N5/8/q7 w - - 0 1")
        pins = detect_pins(board)
        assert any(p.pinned_square == "c3" for p in pins)

    def test_queen_pin_on_file(self) -> None:
        """Black queen e8 pins white bishop e5 to white king e1."""
        board = board_from_fen("4q2k/8/8/4B3/8/8/8/4K3 w - - 0 1")
        pins = detect_pins(board)
        assert len(pins) == 1
        p = pins[0]
        assert p.pinned_square == "e5"
        assert p.pinner_square == "e8"


# ---------------------------------------------------------------------------
# Multiple pins / both sides
# ---------------------------------------------------------------------------


class TestMultiplePins:
    def test_two_pins_on_same_side(self) -> None:
        """Two white pieces pinned simultaneously."""
        # White king e1; black bishop b4 pins white knight c3 (diagonal);
        # black rook e8 pins white bishop e5 (file).
        board = board_from_fen("4r2k/8/8/4B3/1b6/2N5/8/4K3 w - - 0 1")
        pins = detect_pins(board)
        pinned_squares = {p.pinned_square for p in pins}
        assert "c3" in pinned_squares
        assert "e5" in pinned_squares

    def test_both_sides_pinned(self) -> None:
        """Both sides have a pin simultaneously."""
        # Black rook a1 pins white knight c1 to white king d1 (rank).
        # White bishop g5 pins black knight f6 to black king e7 (diagonal).
        board = board_from_fen("8/4k3/5n2/6B1/8/8/8/r1NK4 w - - 0 1")
        pins = detect_pins(board)
        sides = {p.pinned_side for p in pins}
        assert "white" in sides
        assert "black" in sides



# ---------------------------------------------------------------------------
# Evidence model
# ---------------------------------------------------------------------------


class TestPinEvidenceModel:
    def test_is_frozen(self) -> None:
        ev = PinEvidence(
            pinned_side="white",
            pinned_square="c3",
            pinner_square="b4",
            shielded_square="e1",
            is_absolute=True,
        )
        with pytest.raises(Exception):
            ev.pinned_side = "black"  # type: ignore[misc]

    def test_is_absolute_always_true(self) -> None:
        """All pins returned by detect_pins must be absolute."""
        board = board_from_fen("4k3/8/2n5/1B6/8/8/8/4K3 b - - 0 1")
        for p in detect_pins(board):
            assert p.is_absolute is True


# ---------------------------------------------------------------------------
# Property tests
# ---------------------------------------------------------------------------


@given(st.integers(min_value=0, max_value=40))
@settings(max_examples=50)
def test_pinned_squares_are_valid(num_moves: int) -> None:
    """Every pinned/pinner/shielded square must be a valid UCI square name."""
    valid = {chess.square_name(sq) for sq in chess.SQUARES}
    board = chess.Board()
    for _ in range(num_moves):
        legal = list(board.legal_moves)
        if not legal:
            break
        board.push(legal[0])
    for p in detect_pins(board):
        assert p.pinned_square in valid
        assert p.pinner_square in valid
        assert p.shielded_square in valid


@given(st.integers(min_value=0, max_value=40))
@settings(max_examples=50)
def test_pin_geometry_consistent(num_moves: int) -> None:
    """
    For every returned pin, the pinned square must lie between
    the pinner and the shielded (king) square.
    """
    board = chess.Board()
    for _ in range(num_moves):
        legal = list(board.legal_moves)
        if not legal:
            break
        board.push(legal[0])
    for p in detect_pins(board):
        pinner_sq = chess.parse_square(p.pinner_square)
        pinned_sq = chess.parse_square(p.pinned_square)
        king_sq = chess.parse_square(p.shielded_square)
        between = chess.SquareSet(chess.between(pinner_sq, king_sq))
        assert pinned_sq in between, (
            f"Pin geometry broken: {p.pinned_square} not between "
            f"{p.pinner_square} and {p.shielded_square}"
        )
