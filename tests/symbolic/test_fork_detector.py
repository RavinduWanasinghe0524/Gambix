"""
Tests for gambix.symbolic.fork_detector.

Coverage targets
----------------
- No fork           → empty list
- Knight fork (classic: forks king and queen)
- Bishop fork
- Queen fork
- Rook fork
- Pawn attacks two pawns → NOT a fork (below victim threshold)
- Pawn forks two rooks → IS a fork (both ≥ 300 cp)
- attacks_king=True when king is one of the forked pieces
- attacks_king=False when king is not involved
- Both sides can fork simultaneously
- Evidence model is frozen
- Property: forking_square belongs to the forking side
- Property: every forked square has an opponent piece
"""

from __future__ import annotations

import chess
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from gambix.symbolic import ForkEvidence, detect_forks


def board_from_fen(fen: str) -> chess.Board:
    return chess.Board(fen)


# ---------------------------------------------------------------------------
# No fork
# ---------------------------------------------------------------------------


class TestNoFork:
    def test_starting_position(self) -> None:
        assert detect_forks(chess.Board()) == []

    def test_king_vs_king(self) -> None:
        board = board_from_fen("4k3/8/8/8/8/8/8/4K3 w - - 0 1")
        assert detect_forks(board) == []

    def test_pawn_attacks_two_pawns_not_fork(self) -> None:
        """Pawn attacking two pawns is below the victim threshold."""
        # White pawn d5 attacks c6 and e6 (both black pawns) — not a fork
        board = board_from_fen("4k3/8/2p1p3/3P4/8/8/8/4K3 w - - 0 1")
        forks = detect_forks(board)
        assert not any(f.forking_square == "d5" for f in forks)


# ---------------------------------------------------------------------------
# Knight fork
# ---------------------------------------------------------------------------


class TestKnightFork:
    def test_knight_forks_king_and_queen(self) -> None:
        """White knight on c5 forks black king on e6 and queen on a6."""
        # Knight c5 attacks: a4,b3,d3,e4,e6,d7,b7,a6
        # Black king e6, black queen a6 — both attacked by Nc5
        board = board_from_fen("8/8/q3k3/2N5/8/8/8/4K3 w - - 0 1")
        forks = detect_forks(board)
        white_forks = [f for f in forks if f.forking_side == "white"]
        assert len(white_forks) == 1
        f = white_forks[0]
        assert f.forking_square == "c5"
        assert f.attacks_king is True
        assert len(f.forked_squares) >= 2

    def test_knight_fork_no_king(self) -> None:
        """White knight on d5 forks black rook on c7 and bishop on f6."""
        # Knight d5 attacks: c3,e3,b4,f4,b6,f6,c7,e7
        # Black rook c7, black bishop f6
        board = board_from_fen("4k3/2r5/5b2/3N4/8/8/8/4K3 w - - 0 1")
        forks = detect_forks(board)
        white_forks = [f for f in forks if f.forking_side == "white"]
        assert len(white_forks) == 1
        f = white_forks[0]
        assert f.forking_square == "d5"
        assert f.attacks_king is False
        assert "c7" in f.forked_squares
        assert "f6" in f.forked_squares


# ---------------------------------------------------------------------------
# Bishop fork
# ---------------------------------------------------------------------------


class TestBishopFork:
    def test_bishop_forks_two_rooks(self) -> None:
        """White bishop on e4 attacks black rooks on a8 and h7."""
        board = board_from_fen("r6k/7r/8/8/4B3/8/8/4K3 w - - 0 1")
        forks = detect_forks(board)
        white_forks = [f for f in forks if f.forking_side == "white"]
        assert any(f.forking_square == "e4" for f in white_forks)
        fork = next(f for f in white_forks if f.forking_square == "e4")
        assert len(fork.forked_squares) >= 2


# ---------------------------------------------------------------------------
# Queen fork
# ---------------------------------------------------------------------------


class TestQueenFork:
    def test_queen_forks_rook_and_bishop(self) -> None:
        """White queen on d4 attacks black rook on a7 and bishop on g7."""
        board = board_from_fen("8/r5bk/8/8/3Q4/8/8/4K3 w - - 0 1")
        forks = detect_forks(board)
        white_forks = [f for f in forks if f.forking_side == "white"]
        assert any(f.forking_square == "d4" for f in white_forks)


# ---------------------------------------------------------------------------
# Pawn fork (≥ 300 cp victims)
# ---------------------------------------------------------------------------


class TestPawnFork:
    def test_pawn_forks_two_rooks(self) -> None:
        """White pawn on d5 attacks black rooks on c6 and e6."""
        board = board_from_fen("4k3/8/2r1r3/3P4/8/8/8/4K3 w - - 0 1")
        forks = detect_forks(board)
        white_forks = [f for f in forks if f.forking_side == "white"]
        assert any(f.forking_square == "d5" for f in white_forks)


# ---------------------------------------------------------------------------
# attacks_king flag
# ---------------------------------------------------------------------------


class TestAttacksKing:
    def test_attacks_king_true(self) -> None:
        """Fork involving the king must set attacks_king=True."""
        board = board_from_fen("8/8/q3k3/2N5/8/8/8/4K3 w - - 0 1")
        forks = detect_forks(board)
        white_forks = [f for f in forks if f.forking_side == "white"]
        assert any(f.attacks_king for f in white_forks)

    def test_attacks_king_false(self) -> None:
        """Fork not involving the king must set attacks_king=False."""
        board = board_from_fen("4k3/2r5/5b2/3N4/8/8/8/4K3 w - - 0 1")
        forks = detect_forks(board)
        white_forks = [f for f in forks if f.forking_side == "white"]
        assert all(not f.attacks_king for f in white_forks)


# ---------------------------------------------------------------------------
# Both sides
# ---------------------------------------------------------------------------


class TestBothSides:
    def test_both_sides_fork(self) -> None:
        """Both white and black have a fork simultaneously."""
        # White knight d5 forks black rook c7 and bishop e7
        # Black knight f4 forks white rook g2 and bishop h3 (adjusted)
        # Simplified: just check both sides appear in results
        board = board_from_fen("4k3/2rb4/8/3N4/5n2/7B/6R1/4K3 w - - 0 1")
        forks = detect_forks(board)
        sides = {f.forking_side for f in forks}
        assert "white" in sides
        assert "black" in sides


# ---------------------------------------------------------------------------
# Evidence model
# ---------------------------------------------------------------------------


class TestForkEvidenceModel:
    def test_is_frozen(self) -> None:
        ev = ForkEvidence(
            forking_side="white",
            forking_square="d5",
            forked_squares=["c7", "e7"],
            attacks_king=False,
        )
        with pytest.raises(Exception):
            ev.forking_side = "black"  # type: ignore[misc]

    def test_forked_squares_min_length(self) -> None:
        with pytest.raises(Exception):
            ForkEvidence(
                forking_side="white",
                forking_square="d5",
                forked_squares=["c7"],  # only one — invalid
                attacks_king=False,
            )


# ---------------------------------------------------------------------------
# Property tests
# ---------------------------------------------------------------------------


@given(st.integers(min_value=0, max_value=40))
@settings(max_examples=50)
def test_forking_piece_belongs_to_forking_side(num_moves: int) -> None:
    """The forking piece must belong to the declared forking_side."""
    board = chess.Board()
    for _ in range(num_moves):
        legal = list(board.legal_moves)
        if not legal:
            break
        board.push(legal[0])
    for f in detect_forks(board):
        sq = chess.parse_square(f.forking_square)
        piece = board.piece_at(sq)
        assert piece is not None
        expected_color = chess.WHITE if f.forking_side == "white" else chess.BLACK
        assert piece.color == expected_color


@given(st.integers(min_value=0, max_value=40))
@settings(max_examples=50)
def test_forked_squares_have_opponent_pieces(num_moves: int) -> None:
    """Every forked square must contain an opponent piece ≥ 300 cp."""
    board = chess.Board()
    for _ in range(num_moves):
        legal = list(board.legal_moves)
        if not legal:
            break
        board.push(legal[0])
    for f in detect_forks(board):
        victim_color = chess.BLACK if f.forking_side == "white" else chess.WHITE
        for sq_name in f.forked_squares:
            sq = chess.parse_square(sq_name)
            piece = board.piece_at(sq)
            assert piece is not None
            assert piece.color == victim_color
