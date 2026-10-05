import numpy as np
import chess


PIECE_VALUES_64 = {
    chess.PAWN: 0.1,
    chess.KNIGHT: 0.3,
    chess.BISHOP: 0.45,
    chess.ROOK: 0.6,
    chess.QUEEN: 0.8,
    chess.KING: 1.0,
}


def get_numeric_board_pawns_calculation(board_str):
    numeric_dic = {
        'p': -0.1, 'n': -0.32, 'b': -0.333, 'r': -0.51, 'q': -0.92, 'k': -1,
        'P': 0.1, 'N': 0.32, 'B': 0.333, 'R': 0.51, 'Q': 0.92, 'K': 1
    }
    numeric_board = np.zeros(64)  # Initialize as zeros
    n = 0
    for k in board_str:
        if k == '\n' or k == ' ':
            continue
        if k == '.':
            numeric_board[n] = 0
        else:
            piece = numeric_dic[k]
            numeric_board[n] = piece
        n += 1
        if n >= 64:  # Break loop if we reach the end of the board
            break

    return numeric_board


def get_numeric_board_ai_64(board_str=None, board=None):
    """
    Converts board state into a 64-element float array.
    Accepts board (chess.Board) for fast bitboard extraction, or board_str for string parsing.
    """
    if board is not None or (board_str is not None and not isinstance(board_str, str) and hasattr(board_str, 'pieces_mask')):
        b = board if board is not None else board_str
        numeric_board = np.zeros(64, dtype=float)
        for pt, val in PIECE_VALUES_64.items():
            bb_w = b.pieces_mask(pt, chess.WHITE)
            while bb_w:
                sq = (bb_w & -bb_w).bit_length() - 1
                bb_w &= bb_w - 1
                numeric_board[sq ^ 56] = val

            bb_b = b.pieces_mask(pt, chess.BLACK)
            while bb_b:
                sq = (bb_b & -bb_b).bit_length() - 1
                bb_b &= bb_b - 1
                numeric_board[sq ^ 56] = -val

        return numeric_board

    if board_str is None:
        return np.zeros(64, dtype=float)

    numeric_dic_v2 = {
        'p': -0.1, 'n': -0.3, 'b': -0.45, 'r': -0.6, 'q': -0.8, 'k': -1,
        'P': 0.1, 'N': 0.3, 'B': 0.45, 'R': 0.6, 'Q': 0.8, 'K': 1
    }
    numeric_board = np.zeros(64, dtype=float)  # Initialize as zeros
    n = 0
    for k in board_str:
        if k == '\n' or k == ' ':
            continue
        if k == '.':
            numeric_board[n] = 0.0
        else:
            piece = numeric_dic_v2[k]
            numeric_board[n] = piece
        n += 1
        if n >= 64:  # Break loop if we reach the end of the board
            break

    return numeric_board


# 12 piece planes (6 white, 6 black) x 64 squares = 768 binary inputs
PIECE_PLANE_INDICES = {
    'P': 0, 'N': 1, 'B': 2, 'R': 3, 'Q': 4, 'K': 5,
    'p': 6, 'n': 7, 'b': 8, 'r': 9, 'q': 10, 'k': 11
}


def get_numeric_board_ai(board_str=None, board=None):
    """
    Converts board state into a 768 binary input array (12 piece planes x 64 squares).
    Planes 0 to 5: White pieces (P, N, B, R, Q, K)
    Planes 6 to 11: Black pieces (p, n, b, r, q, k)
    Accepts board_str (string) or board (chess.Board).
    """
    numeric_board = np.zeros(768, dtype=float)

    if board is not None or (board_str is not None and not isinstance(board_str, str) and hasattr(board_str, 'piece_at')):
        b = board if board is not None else board_str
        # Fast bitboard extraction matching the square coordinate mapping:
        # rank 7..0, file 0..7 => (7 - rank) * 8 + file == sq ^ 56
        for pt in range(1, 7):
            # White: planes 0..5
            bb_w = b.pieces_mask(pt, chess.WHITE)
            offset_w = (pt - 1) * 64
            while bb_w:
                sq = (bb_w & -bb_w).bit_length() - 1
                bb_w &= bb_w - 1
                numeric_board[offset_w + (sq ^ 56)] = 1.0

            # Black: planes 6..11
            bb_b = b.pieces_mask(pt, chess.BLACK)
            offset_b = (pt + 5) * 64
            while bb_b:
                sq = (bb_b & -bb_b).bit_length() - 1
                bb_b &= bb_b - 1
                numeric_board[offset_b + (sq ^ 56)] = 1.0

        return numeric_board

    if board_str is None:
        return numeric_board

    # Fast parsing directly from board_str (fallback)
    n = 0
    for k in board_str:
        if k == '\n' or k == ' ':
            continue
        if k != '.':
            plane = PIECE_PLANE_INDICES.get(k)
            if plane is not None:
                numeric_board[plane * 64 + n] = 1.0
        n += 1
        if n >= 64:
            break

    return numeric_board

