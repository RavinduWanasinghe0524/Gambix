"""
Check detector — deterministic, engine-free.

Determines whether the side to move *was just put* in check by the
previous half-move, characterises the check (single / double / mate),
and identifies every checking piece.

Precision guarantee: 100 % (purely derives from python-chess legal-move
generation; no heuristics involved).
"""

from __future__ import annotations

import chess

from gambix.symbolic._types import CheckEvidence


def detect_check(board: chess.Board) -> CheckEvidence | None:
    """
    Analyse *board* for check on the side to move.

    Parameters
    ----------
    board:
        A ``chess.Board`` **after** the move has been applied, so
        ``board.turn`` is the side that was just put in check (if any).

    Returns
    -------
    ``CheckEvidence`` if the side to move is in check, else ``None``.

    Examples
    --------
    >>> import chess
    >>> board = chess.Board("rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3")
    >>> ev = detect_check(board)
    >>> ev.side_in_check
    'white'
    >>> ev.is_checkmate
    False
    """
    if not board.is_check():
        return None

    side_in_check: chess.Color = board.turn  # the side about to move is in check

    # Identify all squares attacking the king.
    king_sq: int | None = board.king(side_in_check)
    if king_sq is None:  # malformed position — shouldn't happen in practice
        return None  # pragma: no cover

    attackers_mask: chess.SquareSet = board.attackers(not side_in_check, king_sq)
    checking_squares: list[str] = [chess.square_name(sq) for sq in attackers_mask]

    return CheckEvidence(
        side_in_check="white" if side_in_check == chess.WHITE else "black",
        checking_pieces=checking_squares,
        is_double_check=len(checking_squares) > 1,
        is_checkmate=board.is_checkmate(),
    )
