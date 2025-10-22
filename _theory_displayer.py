
from aux_funcs_random import getPickleData

THEORY_DICT_PATH = r"aux_files/massive_theory.dict"

d = getPickleData(THEORY_DICT_PATH)

print()
for key in d:
    print(f"{key}: {d[key]}")

print()
