from aux_openings_massive_dict import getTheoryDB, store_full_dict

DISABLE_OPENINGS = True

"""
Super Strong Openings:
- Ruy Lopez
- Najdorf
- Berlin Defense
- Sicilian Defense
- Queens Gambit
- Petrov
"""


def get_starting_moves_white(force_openings=False):
    if DISABLE_OPENINGS and not force_openings:
        return None
    else:
        return ['d2d4', 'e2e4', 'g1f3', 'c2c4', 'g2g3']


def theory_opening(board):

    theory = getTheoryDB()

    if DISABLE_OPENINGS:
        return None

    # INPUT - SETUP
    aux_fen = board.fen()
    aux2 = aux_fen.split('-')
    current_fen = aux2[0][:-1]

    return theory.getBestMove(current_fen)



def check_if_in_dict(dict_to_check):
    dict_new_moves = {}
    dict_old_moves = {}
    inserted_counts = [0, 0]

    for fen in dict_to_check:
        if fen == 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq':     # ignore
            continue
        if get_full_dict_response(fen) is None:
            dict_new_moves[fen] = dict_to_check[fen]
            inserted_counts[0] += 1
        else:
            response = get_full_dict_response(fen)
            if isinstance(response, str) and (dict_to_check[fen] == response):
                continue
            elif dict_to_check[fen] in response:
                continue
            else:
                dict_old_moves[fen] = dict_to_check[fen]
                inserted_counts[1] += 1


    print()

    for fen in dict_new_moves:
        print(f"theory['{fen}'] = '{dict_new_moves[fen]}'")

    if dict_old_moves:
        print("\n\n\n")
        for fen in dict_old_moves:
            print(fen)

    print(f"\n\n\nnew moves = {inserted_counts[0]}/{inserted_counts[0] + inserted_counts[1]}")



if __name__ == '__main__':
    theory = {}

    check_if_in_dict(theory)

