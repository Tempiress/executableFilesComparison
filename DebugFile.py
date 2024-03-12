from opcodeparser import *
from blocklinks4 import *
from renamefile import *
from  linkMatrix import *


# r = rename_block('D:\\MyNauchWork\\cfg\\cfg_5368778762.txt', 'D:\\MyNauchWork\\cfg\\cfg_5368778977.txt')
#print(block_links_pro(r))


# 1.
op = op_parser('D:\\MyNauchWork\\cfg\\cfg_5368778762.txt')
print("op_parcer \n", op)
op2 = op_parser('D:\\MyNauchWork\\cfg\\cfg_5368778977.txt')

# 2.
fsb = find_similar_blocks(op, op2)
print("Find similar blocks: \n", fsb)

# 3.
block_links(op)
bl = rename_block(op, op2)

# 4.
rename_block(op, op2)

# 5.
#create_matrix()
