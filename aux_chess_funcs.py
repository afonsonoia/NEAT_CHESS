
def convert_chess_notation_to_sq_number(notation):
    num_inicial = 0
    num_final = 0
    if len(notation) == 4:
        num_inicial = ord(notation[0]) - 97
        num_inicial += (int(notation[1]) - 1) * 8
        num_final = ord(notation[2]) - 97
        num_final += (int(notation[3]) - 1) * 8
        return [num_inicial, num_final]
    elif len(notation) == 5:
        num_inicial = ord(notation[0]) - 97
        num_inicial += (int(notation[1]) - 1) * 8
        num_final = ord(notation[2]) - 97
        num_final += (int(notation[3]) - 1) * 8
        return [num_inicial, num_final, notation[4]]


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