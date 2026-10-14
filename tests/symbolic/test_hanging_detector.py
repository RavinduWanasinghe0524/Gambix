"""
Tests for gambix.symbolic.hanging_detector.

Coverage targets
----------------
- No hanging pieces    → empty list
- Undefended attacked piece → hanging
- Attacked piece with equal defenders → NOT hanging (defenders == attackers)
- Attacked piece with more defenders → NOT hanging
- Kings are never hanging
- Both sides can have hanging pieces
- piece_value_cp is correct for each piece type
- attacker_count / defender_count are accurate
- Evidence model is frozen
- Property: hanging piece always has attacker_count > defender_count
- Property: hanging side matches actual piece colour on board
"""

from __future__ import annotations

import chess
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from gambix.symbolic import HangingPieceEvidence, detect_hanging_pieces


def board_from_fen(fen: str) -> chess.Board:
    return chess.Board(fen)


# ---------------------------------------------------------------------------
# No hanging pieces
# ---------------------------------------------------------------------------


class TestNoHanging:
    def test_starting_position(self) -> None:
        assert detect_hanging_pieces(chess.Board()) == []

    def test_all_pieces_defended(self) -> None:
        """Black bishop e6 attacked by white bishop b3, defended by black rook e8."""
        board = board_from_fen("4r2k/8/4b3/8/8/1B6/8/4K3 w - - 0 1")
        # attacker: Bb3 (1), defender: Re8 (1) → not hanging
        results = detect_hanging_pieces(board)
        assert not any(r.hanging_square == "e6" for r in results)

    def test_defended_more_than_attacked(self) -> None:
        """Two defenders vs one attacker — not hanging."""
        # White knight e5 attacked by one black pawn (d6), defended by two white rooks
        board = board_from_fen("4k3/8/3p4/4N3/8/8/4R3/4RK2 w - - 0 1")
        results = detect_hanging_pieces(board)
        assert not any(r.hanging_square == "e5" for r in results)


# ---------------------------------------------------------------------------
# Hanging pieces
# ---------------------------------------------------------------------------


class TestHangingPieces:
    def test_undefended_knight(self) -> None:
        """White knight e5 attacked by black pawn d6, no defenders."""
        board = board_from_fen("4k3/8/3p4/4N3/8/8/8/4K3 w - - 0 1")
        results = detect_hanging_pieces(board)
        assert len(results) == 1
        h = results[0]
        assert h.hanging_side == "white"
        assert h.hanging_square == "e5"
        assert h.piece_value_cp == 300
        assert h.attacker_count == 1
        assert h.defender_count == 0

    def test_undefended_queen(self) -> None:
        """Black queen d5 attacked by white rook d1, no defenders."""
        board = board_from_fen("4k3/8/8/3q4/8/8/8/3RK3 w - - 0 1")
        results = detect_hanging_pieces(board)
        assert any(r.hanging_square == "d5" and r.piece_value_cp == 900 for r in results)

    def test_undefended_bishop(self) -> None:
        """White bishop f4 attacked by black knight e6, no defenders."""
        board = board_from_fen("4k3/8/4n3/8/5B2/8/8/4K3 w - - 0 1")
        results = detect_hanging_pieces(board)
        assert any(r.hanging_square == "f4" and r.piece_value_cp == 300 for r in results)

    def test_undefended_rook(self) -> None:
        """White rook e5 attacked by two black pieces from different directions."""
        # Black queen h5 attacks e5 along rank; black bishop b2 attacks e5 diagonally.
        # No white defenders of e5.
        board = board_from_fen("6k1/8/8/4R2q/8/8/1b6/4K3 w - - 0 1")
        results = detect_hanging_pieces(board)
        rook_result = next((r for r in results if r.hanging_square == "e5"), None)
        assert rook_result is not None
        assert rook_result.piece_value_cp == 500
        assert rook_result.attacker_count >= 2

    def test_attacker_outnumbers_defender(self) -> None:
        """Two attackers vs one defender → hanging."""
        # White knight e5: attacked by black queen h5 (rank) and black bishop b2 (diagonal),
        # defended only by white rook e1.
        board = board_from_fen("6k1/8/8/4N2q/8/8/1b6/4RK2 w - - 0 1")
        results = detect_hanging_pieces(board)
        ne5 = next((r for r in results if r.hanging_square == "e5"), None)
        assert ne5 is not None
        assert ne5.attacker_count > ne5.defender_count


# ---------------------------------------------------------------------------
# Kings never hanging
# ---------------------------------------------------------------------------


class TestKingsNotHanging:
    def test_king_not_in_results(self) -> None:
        """Even if a king is "attacked", it must never appear in hanging results."""
        # Black king on h8 attacked by white rook h1 (that's check, not hanging)
        board = board_from_fen("7k/8/8/8/8/8/8/6RK b - - 0 1")
        results = detect_hanging_pieces(board)
        assert not any(r.hanging_square in ("h8", "h1") and r.piece_value_cp == 20000
                       for r in results)
        king_squares = {"a1", "b1", "c1", "d1", "e1", "f1", "g1", "h1",
                        "a8", "b8", "c8", "d8", "e8", "f8", "g8", "h8"}
        for r in results:
            piece = board.piece_at(chess.parse_square(r.hanging_square))
            assert piece is not None
            assert piece.piece_type != chess.KING


# ---------------------------------------------------------------------------
# Both sides
# ---------------------------------------------------------------------------


class TestBothSides:
    def test_both_sides_have_hanging_pieces(self) -> None:
        """Both white and black have at least one hanging piece."""
        # White knight e5: attacked by black pawn d6, not defended.
        # Black bishop c6: attacked by white knight e5 (Nc5 attacks d7,b7,a5,e4 but NOT c6 from e5).
        # Use: Black bishop g4 attacked by white pawn h3, not defended.
        board = board_from_fen("4k3/8/3p4/4N3/6b1/7P/8/4K3 w - - 0 1")
        results = detect_hanging_pieces(board)
        sides = {r.hanging_side for r in results}
        assert "white" in sides
        assert "black" in sides


# ---------------------------------------------------------------------------
# Piece values
# ---------------------------------------------------------------------------


class TestPieceValues:
    @pytest.mark.parametrize("fen,square,expected_cp", [
        ("4k3/8/3p4/4N3/8/8/8/4K3 w - - 0 1",  "e5", 300),  # knight
        ("4k3/8/3p4/4B3/8/8/8/4K3 w - - 0 1",  "e5", 300),  # bishop
        ("6k1/8/8/3q4/8/8/8/3RK3 b - - 0 1",   "d5", 900),  # queen attacked by rook, no defenders
        ("6k1/8/8/8/3R4/8/1q6/5K2 w - - 0 1",  "d4", 500),  # rook attacked by queen, no defenders
        ("3r2k1/8/8/3Q4/8/8/8/5K2 b - - 0 1",  "d5", 900),  # queen attacked by rook
    ])
    def test_piece_value_cp(self, fen: str, square: str, expected_cp: int) -> None:
        board = board_from_fen(fen)
        results = detect_hanging_pieces(board)
        target = next((r for r in results if r.hanging_square == square), None)
        assert target is not None, f"Expected {square} to be hanging in {fen}"
        assert target.piece_value_cp == expected_cp


# ---------------------------------------------------------------------------
# Evidence model
# ---------------------------------------------------------------------------


class TestHangingEvidenceModel:
    def test_is_frozen(self) -> None:
        ev = HangingPieceEvidence(
            hanging_side="white",
            hanging_square="e5",
            piece_value_cp=300,
            attacker_count=1,
            defender_count=0,
        )
        with pytest.raises(Exception):
            ev.hanging_side = "black"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Property tests
# ---------------------------------------------------------------------------


@given(st.integers(min_value=0, max_value=40))
@settings(max_examples=50)
def test_attacker_always_exceeds_defender(num_moves: int) -> None:
    """attacker_count > defender_count must hold for every result."""
    board = chess.Board()
    for _ in range(num_moves):
        legal = list(board.legal_moves)
        if not legal:
            break
        board.push(legal[0])
    for h in detect_hanging_pieces(board):
        assert h.attacker_count > h.defender_count


@given(st.integers(min_value=0, max_value=40))
@settings(max_examples=50)
def test_hanging_side_matches_board(num_moves: int) -> None:
    """hanging_side must match the colour of the piece on that square."""
    board = chess.Board()
    for _ in range(num_moves):
        legal = list(board.legal_moves)
        if not legal:
            break
        board.push(legal[0])
    for h in detect_hanging_pieces(board):
        sq = chess.parse_square(h.hanging_square)
        piece = board.piece_at(sq)
        assert piece is not None
        expected = "white" if piece.color == chess.WHITE else "black"
        assert h.hanging_side == expected
