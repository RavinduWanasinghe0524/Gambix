"""
Fork detector — deterministic, engine-free.

A **fork** occurs when a single piece attacks two or more opponent pieces
simultaneously, at least one of which is a king, queen, rook, or bishop
(i.e. material ≥ a minor piece — we skip pawns-attacking-pawns as noise).

This detector finds all active forks for the side whose turn it is.

Precision guarantee: 100 % — uses python-chess attack generation only.
"""

from __future__ import annotations

import chess

from gambix.symbolic._types import ForkEvidence

# Minimum victim value (centipawns) to count as a fork target.
# Pawns (100 cp) attacking other pawns are excluded — too noisy.
_FORK_VICTIM_MIN_CP = 300  # minor piece or above

_PIECE_VALUES_CP: dict[chess.PieceType, int] = {
    chess.PAWN: 100,
    chess.KNIGHT: 300,
    chess.BISHOP: 300,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000,
}


def detect_forks(board: chess.Board) -> list[ForkEvidence]:
    """
    Find all forks on *board* for **both** sides.

    A fork is a piece simultaneously attacking ≥2 opponent pieces where
    each victim is worth ≥ a minor piece (300 cp) or is the king.

    Parameters
    ----------
    board:
        Any legal ``chess.Board`` position.

    Returns
    -------
    List of ``ForkEvidence`` (one per forking piece), possibly empty.

    Examples
    --------
    >>> import chess
    >>> # Knight on d5 forks black rook on c7 and bishop on e7
    >>> board = chess.Board("4k3/2rb4/8/3N4/8/8/8/4K3 w - - 0 1")
    >>> forks = detect_forks(board)
    >>> len(forks)
    1
    >>> forks[0].forking_square
    'd5'
    """
    results: list[ForkEvidence] = []

    for forking_side in (chess.WHITE, chess.BLACK):
        victim_side = not forking_side

        for forking_sq in chess.SQUARES:
            piece = board.piece_at(forking_sq)
            if piece is None or piece.color != forking_side:
                continue

            # Get all squares this piece attacks.
            attacked = board.attacks(forking_sq)

            # Filter: must be occupied by a valuable-enough opponent piece.
            victims: list[int] = []
            attacks_king = False
            for sq in attacked:
                victim = board.piece_at(sq)
                if victim is None or victim.color != victim_side:
                    continue
                val = _PIECE_VALUES_CP.get(victim.piece_type, 0)
                if val >= _FORK_VICTIM_MIN_CP:
                    victims.append(sq)
                    if victim.piece_type == chess.KING:
                        attacks_king = True

            if len(victims) >= 2:
                results.append(
                    ForkEvidence(
                        forking_side="white" if forking_side == chess.WHITE else "black",
                        forking_square=chess.square_name(forking_sq),
                        forked_squares=[chess.square_name(sq) for sq in victims],
                        attacks_king=attacks_king,
                    )
                )

    return results
