"""
Pin detector — deterministic, engine-free.

An **absolute pin** exists when a sliding piece (bishop, rook, queen) of
the opponent is attacking a friendly piece, and that friendly piece sits
exactly between the slider and the friendly king on a rank, file, or diagonal.
Moving the pinned piece would expose the king to check (illegal under the rules).

This detector finds all absolute pins for both sides.

Precision guarantee: 100 % — derived entirely from python-chess attack/ray
tables; no heuristics.
"""

from __future__ import annotations

import chess

from gambix.symbolic._types import PinEvidence

# Sliding piece types that can create pins.
_SLIDERS = {chess.BISHOP, chess.ROOK, chess.QUEEN}


def _ray_between(sq_a: int, sq_b: int) -> chess.SquareSet:
    """Return squares strictly between sq_a and sq_b on the same ray, or empty."""
    return chess.SquareSet(chess.between(sq_a, sq_b))


def detect_pins(board: chess.Board) -> list[PinEvidence]:
    """
    Find all absolute pins on *board* for both sides.

    A piece is absolutely pinned when:
      1. It is on the ray between an opponent's slider and its own king.
      2. No other piece stands between the slider and the pinned piece.
      3. No other piece stands between the pinned piece and its king.

    Parameters
    ----------
    board:
        Any legal ``chess.Board`` position.

    Returns
    -------
    List of ``PinEvidence`` (one per pinned piece), possibly empty.

    Examples
    --------
    >>> import chess
    >>> # Classic absolute pin: white bishop on b5 pins black knight on c6 to king e8
    >>> board = chess.Board("4k3/8/2n5/1B6/8/8/8/4K3 b - - 0 1")
    >>> pins = detect_pins(board)
    >>> len(pins)
    1
    >>> pins[0].pinned_square
    'c6'
    """
    results: list[PinEvidence] = []

    for pinned_side in (chess.WHITE, chess.BLACK):
        pinner_side = not pinned_side
        king_sq = board.king(pinned_side)
        if king_sq is None:
            continue  # pragma: no cover

        # Iterate over every sliding piece of the opponent.
        for pinner_sq in board.pieces(chess.BISHOP, pinner_side) | \
                         board.pieces(chess.ROOK, pinner_side) | \
                         board.pieces(chess.QUEEN, pinner_side):

            pinner_piece = board.piece_at(pinner_sq)
            if pinner_piece is None:
                continue  # pragma: no cover

            # Check if king and pinner are on the same ray.
            # chess.between() returns an empty SquareSet when not on the same ray.
            between = _ray_between(pinner_sq, king_sq)
            if not between:
                continue

            # Verify the slider can actually attack along this ray
            # (bishops only on diagonals, rooks only on ranks/files).
            piece_type = pinner_piece.piece_type
            king_file, king_rank = chess.square_file(king_sq), chess.square_rank(king_sq)
            pin_file, pin_rank = chess.square_file(pinner_sq), chess.square_rank(pinner_sq)

            same_rank = king_rank == pin_rank
            same_file = king_file == pin_file
            same_diag = (
                abs(king_file - pin_file) == abs(king_rank - pin_rank)
            )

            if piece_type == chess.ROOK and not (same_rank or same_file):
                continue
            if piece_type == chess.BISHOP and not same_diag:
                continue
            # QUEEN covers all three cases.

            # Count pieces of the pinned_side in the between squares.
            friendly_in_between = [
                sq for sq in between
                if board.color_at(sq) == pinned_side
            ]
            # Count all pieces (any colour) in between.
            total_in_between = [sq for sq in between if board.piece_at(sq) is not None]

            # Pin condition: exactly one friendly piece between slider and king,
            # and no other pieces anywhere in the ray.
            if len(friendly_in_between) == 1 and len(total_in_between) == 1:
                pinned_sq = friendly_in_between[0]
                results.append(
                    PinEvidence(
                        pinned_side="white" if pinned_side == chess.WHITE else "black",
                        pinned_square=chess.square_name(pinned_sq),
                        pinner_square=chess.square_name(pinner_sq),
                        shielded_square=chess.square_name(king_sq),
                        is_absolute=True,
                    )
                )

    return results
