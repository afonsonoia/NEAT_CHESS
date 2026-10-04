
def convert_chess_notation_to_sq_number(notation):
    start_sq = 0
    end_sq = 0
    if len(notation) == 4:
        start_sq = ord(notation[0]) - 97
        start_sq += (int(notation[1]) - 1) * 8
        end_sq = ord(notation[2]) - 97
        end_sq += (int(notation[3]) - 1) * 8
        return [start_sq, end_sq]
    elif len(notation) == 5:
        start_sq = ord(notation[0]) - 97
        start_sq += (int(notation[1]) - 1) * 8
        end_sq = ord(notation[2]) - 97
        end_sq += (int(notation[3]) - 1) * 8
        return [start_sq, end_sq, notation[4]]


def get_all_legal_moves(board):
    arr_possible_moves = []
    aux_arr_debug = []
    for move in board.legal_moves:
        if (len(move.__str__()) == 4) or (len(move.__str__()) == 5):
            aux_arr_debug.append(move.__str__())
            move = convert_chess_notation_to_sq_number(str(move))
            arr_possible_moves.append(move)

    return arr_possible_moves


def get_all_legal_moves_str(board):
    n = []
    r = get_all_legal_moves_raw(board)
    for m in r:
        n.append(m.__str__())
    return n


def get_all_legal_moves_raw(board):
    arr_moves = []
    for move in board.legal_moves:
        arr_moves.append(move)
    return arr_moves