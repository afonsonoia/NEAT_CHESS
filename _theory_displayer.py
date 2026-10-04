
import os
from aux_funcs_random import getPickleData

THEORY_DICT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aux_files", "massive_theory.dict")

d = getPickleData(THEORY_DICT_PATH)

print()
for key in d:
    print(f"{key}: {d[key]}")

print()
