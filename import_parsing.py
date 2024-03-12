import json
import os


def imp_parse(folder):
    files1 = os.listdir(folder)
    j = {}
    k = 0
    for n in files1:
        # print(n[4:-4:])
        j[k] = {n[4:-4:]}
        k += 1
        #print(j)
    #return json.dumps(j)



j = imp_parse("F:\\programming 2024\\Sci_Research\\cfg")