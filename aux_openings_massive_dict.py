
THEORY_DICT_PATH = r"aux_files/massive_theory.dict"


def store_full_dict(dict):
    from aux_funcs_random import savePickleData

    if not dict:
        print("ERROR: attempted to save empty dictionary - aux_openings_massive_dict.py")
        exit(0)
    else:
        savePickleData(THEORY_DICT_PATH, dict)
    return None


def getTheoryDB():
    from aux_funcs_random import getPickleData
    return getPickleData(THEORY_DICT_PATH)
