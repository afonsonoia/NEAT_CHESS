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


def get_numeric_board_ai(board_str):
    numeric_dic_v2 = {
        'p': -0.1, 'n': -0.3, 'b': -0.45, 'r': -0.6, 'q': -0.8, 'k': -1,
        'P': 0.1, 'N': 0.3, 'B': 0.45, 'R': 0.6, 'Q': 0.8, 'K': 1
    }
    numeric_board = np.zeros(64)  # Initialize as zeros
    n = 0
    for k in board_str:
        if k == '\n' or k == ' ':
            continue
        if k == '.':
            numeric_board[n] = 0
        else:
            piece = numeric_dic_v2[k]
            numeric_board[n] = piece
        n += 1
        if n >= 64:  # Break loop if we reach the end of the board
            break

    return numeric_board

