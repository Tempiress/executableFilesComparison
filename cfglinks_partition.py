import json
import os
from opcodeparser import *
import numpy as np


def cfglinks_partition(path):
    with open(path, 'r') as f:
        text = f.read()
        data = json.loads(text)

    size_matr = (len(data), len(data))
    matr = np.zeros(size_matr)
    l = len(data)

    for c in range(len(data)):
        matr[0][c] = data[c]["name"]

    print(matr)




cfglinks_partition("cfgcflinks.txt")



