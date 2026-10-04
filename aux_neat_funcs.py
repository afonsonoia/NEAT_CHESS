import numpy as np


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


def get_numeric_board_ai_64(board_str):
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
        # Direct coordinate mapping to match board.__str__() square order
        for rank in range(7, -1, -1):
            sq_row_offset = (7 - rank) * 8
            for file in range(8):
                sq = (rank << 3) | file
                piece = b.piece_at(sq)
                if piece:
                    plane = PIECE_PLANE_INDICES.get(piece.symbol())
                    if plane is not None:
                        numeric_board[plane * 64 + (sq_row_offset + file)] = 1.0
        return numeric_board

    if board_str is None:
        return numeric_board

    # Fast parsing directly from board_str
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

