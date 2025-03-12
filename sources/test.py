import os
import numpy as np
import hashlib
from similarity import similarity
from opcodeparser import  op_parser
# fi = 'cfg'
# files1 = os.path.join(os.path.abspath(os.curdir),"_" ,fi)
# files1 = os.path.abspath(os.curdir) + "_" + fi
# print(files1)

# lstr = "cfg_5368778757.txt:cfg_5368778757.txt"
#
# print(lstr.split(":")[0])
#
# P1 = os.listdir("F:\\programming 2024\\Sci_Research\\testfolder")
#
#
# delStr = "cfg_5368778762.txt:ABC"
# print(P1)
# P1.remove(delStr.split(":")[0])
#
# print(len(P1))
#
#
# print('-----------')


# def swap_columns(matrix, col1, col2):
#     for row in matrix:
#         row[col1], row[col2] = row[col2], row[col1]
#
# def swap_rows(matrix, row1, row2):
#     m1 = matrix[row1]
#     m2 = matrix[row2]
#
#     matrix[row1] = m2
#     matrix[row2] = m1
#


# matrix = [
#     [1, 2, 3],
#     [4, 5, 6],
#     [7, 8, 9]
# ]
#
# swap_rows(matrix, 0, 2)
#
#
# arr = [[1, 3, 5],
#        [7, 9, 6],
#        [3, 5, 9]]
#
# arr = np.array(arr)
# print('a')
# s = arr[:, 1]
# print(s)

s = 'hei'
s = s.encode()
# hash_object = hashlib.sha224(s)
# hex_dig = hash_object.hexdigest()
#
# print(hex_dig)

#MD5


#hash_object = hashlib.md5(s)
#print(hash_object.hexdigest())

#Test Similarity
# file1 = '.\\C++programs\\cfgs1\\entry0.txt'
# file2 = '.\\C++programs\\cfgs1\\fcn.140011258.txt'
# ssim, lndf = similarity(file1, file2)
# print(ssim)
# print(lndf)

print('----------')

# print(op_parser(file2))
# similar_blocks = {}
#
# similar_blocks[0] = {
#     'block': 1,
#     'similar_to': 2,
#     'simcount': 3,
#     'simequal': 4
# }
#
# del similar_blocks[]
#
# print(len(similar_blocks) == 0)


my_dict = {3: {'block': '2', 'simcount': 100, 'simequal': 1, 'similar_to': '2'}}
first_key, first_value = my_dict.popitem()
my_dict[first_key] = first_value

print("Первый ключ:", first_key)
print("Первое значение:", first_value)

