"""
Tests for gambix.symbolic.check_detector.

Coverage targets
----------------
- No check             → None
- Single check         → CheckEvidence with 1 checking piece
- Double check         → CheckEvidence with is_double_check=True
- Checkmate            → CheckEvidence with is_checkmate=True
- Stalemate            → None  (not check)
- Checking piece names match the actual board
- Property: detect_check is consistent with board.is_check()
- Property: is_double_check iff len(checking_pieces) > 1
- Property: is_checkmate implies is_double_check OR single check
- Property: if is_checkmate, board.is_checkmate() is True
"""

from __future__ import annotations

import chess
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from gambix.symbolic import CheckEvidence, detect_check


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def board_from_fen(fen: str) -> chess.Board:
    return chess.Board(fen)


# ---------------------------------------------------------------------------
# Unit tests — no check
# ---------------------------------------------------------------------------


class TestNoCheck:
    def test_starting_position_returns_none(self) -> None:
        """Standard starting position has no check."""
        board = chess.Board()
        assert detect_check(board) is None

    def test_quiet_midgame_returns_none(self) -> None:
        """A non-check midgame position returns None."""
        # Ruy López after 3.Bb5
        board = board_from_fen(
            "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3"
        )
        assert detect_check(board) is None

    def test_stalemate_returns_none(self) -> None:
        """Stalemate is not check."""
        # Classic stalemate: black king a8, white queen b6, white king c6
        board = board_from_fen("k7/8/1QK5/8/8/8/8/8 b - - 0 1")
        assert detect_check(board) is None


# ---------------------------------------------------------------------------
# Unit tests — single check
# ---------------------------------------------------------------------------


class TestSingleCheck:
    def test_queen_check_not_mate(self) -> None:
        """Black queen on h4 gives check to white king on e1 — not checkmate."""
        # White: king e1, rook d1, bishop f1.  Black: king e8, queen h4.
        # Qh4 attacks e1 diagonally.  White can block with Rd1-d2 or Bf1-g2, not mate.
        board = board_from_fen("4k3/8/8/8/7q/8/8/3RKB2 w - - 0 1")
        ev = detect_check(board)
        assert ev is not None
        assert isinstance(ev, CheckEvidence)
        assert ev.side_in_check == "white"
        assert ev.is_double_check is False
        assert ev.is_checkmate is False
        assert "h4" in ev.checking_pieces
        assert len(ev.checking_pieces) == 1


    def test_black_king_in_check(self) -> None:
        """White rook on e1 checks the black king on e8."""
        board = board_from_fen("4k3/8/8/8/8/8/8/4R2K b - - 0 1")
        ev = detect_check(board)
        assert ev is not None
        assert ev.side_in_check == "black"
        assert "e1" in ev.checking_pieces
        assert ev.is_double_check is False
        assert ev.is_checkmate is False

    def test_check_by_bishop(self) -> None:
        """Bishop on b5 gives check to the black king on e8."""
        board = board_from_fen("4k3/8/8/1B6/8/8/8/4K3 b - - 0 1")
        ev = detect_check(board)
        assert ev is not None
        assert ev.side_in_check == "black"
        assert "b5" in ev.checking_pieces

    def test_check_by_knight(self) -> None:
        """Knight on f6 gives check to the black king on e8."""
        board = board_from_fen("4k3/8/5N2/8/8/8/8/4K3 b - - 0 1")
        ev = detect_check(board)
        assert ev is not None
        assert ev.side_in_check == "black"
        assert "f6" in ev.checking_pieces


# ---------------------------------------------------------------------------
# Unit tests — double check
# ---------------------------------------------------------------------------


class TestDoubleCheck:
    def test_double_check_detected(self) -> None:
        """
        Discovered double check: bishop on b5 + rook on e1 both check e8.
        Constructed carefully: it's black's turn and two white pieces attack e8.
        """
        # White rook e1 + white bishop b5 both attack black king e8
        board = board_from_fen("4k3/8/8/1B6/8/8/8/4R2K b - - 0 1")
        ev = detect_check(board)
        assert ev is not None
        assert ev.is_double_check is True
        assert len(ev.checking_pieces) == 2
        assert "e1" in ev.checking_pieces
        assert "b5" in ev.checking_pieces

    def test_double_check_side_in_check(self) -> None:
        board = board_from_fen("4k3/8/8/1B6/8/8/8/4R2K b - - 0 1")
        ev = detect_check(board)
        assert ev is not None
        assert ev.side_in_check == "black"


# ---------------------------------------------------------------------------
# Unit tests — checkmate
# ---------------------------------------------------------------------------


class TestCheckmate:
    def test_scholars_mate(self) -> None:
        """Scholar's Mate: 1.e4 e5 2.Qh5 Nc6 3.Bc4 Nf6?? 4.Qxf7#"""
        board = chess.Board()
        for move in ["e2e4", "e7e5", "d1h5", "b8c6", "f1c4", "g8f6", "h5f7"]:
            board.push(chess.Move.from_uci(move))
        ev = detect_check(board)
        assert ev is not None
        assert ev.is_checkmate is True
        assert ev.side_in_check == "black"

    def test_back_rank_mate(self) -> None:
        """Back-rank mate: white rook on e8 mates black king on g8."""
        # Black king g8, own pawns on f7/g7/h7 block escape, white rook e8.
        board = board_from_fen("4R1k1/5ppp/8/8/8/8/8/6K1 b - - 0 1")
        ev = detect_check(board)
        assert ev is not None
        assert ev.is_checkmate is True

    def test_smothered_mate(self) -> None:
        """Smothered mate: knight on f7 mates black king on h8."""
        # Black king h8, own pieces g8/h7, white knight f7 → smothered
        board = board_from_fen("6rk/5Npp/8/8/8/8/8/6K1 b - - 0 1")
        ev = detect_check(board)
        assert ev is not None
        assert ev.is_checkmate is True
        assert ev.is_double_check is False

    def test_checkmate_implies_check(self) -> None:
        """If is_checkmate is True, the board must also be in check."""
        board = board_from_fen("4R1k1/5ppp/8/8/8/8/8/6K1 b - - 0 1")
        ev = detect_check(board)
        assert ev is not None
        assert board.is_check()

    def test_checkmate_piece_recorded(self) -> None:
        """The mating piece must appear in checking_pieces."""
        board = board_from_fen("4R1k1/5ppp/8/8/8/8/8/6K1 b - - 0 1")
        ev = detect_check(board)
        assert ev is not None
        assert "e8" in ev.checking_pieces


# ---------------------------------------------------------------------------
# Unit tests — evidence model integrity
# ---------------------------------------------------------------------------


class TestEvidenceModel:
    def test_evidence_is_frozen(self) -> None:
        """CheckEvidence must be immutable (frozen Pydantic model)."""
        ev = CheckEvidence(
            side_in_check="white",
            checking_pieces=["h4"],
            is_double_check=False,
            is_checkmate=False,
        )
        with pytest.raises(Exception):
            ev.side_in_check = "black"  # type: ignore[misc]

    def test_checking_pieces_min_length(self) -> None:
        """checking_pieces must have at least one entry."""
        with pytest.raises(Exception):
            CheckEvidence(
                side_in_check="white",
                checking_pieces=[],
                is_double_check=False,
                is_checkmate=False,
            )


# ---------------------------------------------------------------------------
# Property-based tests (Hypothesis)
# ---------------------------------------------------------------------------


@given(st.integers(min_value=0, max_value=50))
@settings(max_examples=50)
def test_detect_check_consistent_with_board_is_check(num_moves: int) -> None:
    """
    For any legal game position, detect_check returns non-None iff
    board.is_check() is True.
    """
    board = chess.Board()
    for _ in range(num_moves):
        legal = list(board.legal_moves)
        if not legal:
            break
        board.push(legal[0])  # deterministic: always push first legal move

    ev = detect_check(board)
    if board.is_check():
        assert ev is not None, "Expected evidence for in-check position"
    else:
        assert ev is None, "Expected None for non-check position"


@given(st.integers(min_value=1, max_value=60))
@settings(max_examples=50)
def test_is_double_check_matches_piece_count(num_moves: int) -> None:
    """
    is_double_check must be True iff len(checking_pieces) > 1.
    """
    board = chess.Board()
    for _ in range(num_moves):
        legal = list(board.legal_moves)
        if not legal:
            break
        board.push(legal[0])

    ev = detect_check(board)
    if ev is not None:
        assert ev.is_double_check == (len(ev.checking_pieces) > 1)


@given(st.integers(min_value=1, max_value=60))
@settings(max_examples=50)
def test_is_checkmate_consistent_with_board(num_moves: int) -> None:
    """
    ev.is_checkmate must match board.is_checkmate().
    """
    board = chess.Board()
    for _ in range(num_moves):
        legal = list(board.legal_moves)
        if not legal:
            break
        board.push(legal[0])

    ev = detect_check(board)
    if ev is not None:
        assert ev.is_checkmate == board.is_checkmate()


@given(st.integers(min_value=1, max_value=60))
@settings(max_examples=50)
def test_checking_pieces_are_valid_squares(num_moves: int) -> None:
    """
    All squares in checking_pieces must be valid UCI square names (a1–h8).
    """
    valid_squares = {chess.square_name(sq) for sq in chess.SQUARES}
    board = chess.Board()
    for _ in range(num_moves):
        legal = list(board.legal_moves)
        if not legal:
            break
        board.push(legal[0])

    ev = detect_check(board)
    if ev is not None:
        for sq in ev.checking_pieces:
            assert sq in valid_squares, f"Invalid square name: {sq!r}"
