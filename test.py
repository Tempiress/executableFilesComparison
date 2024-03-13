import os

fi = 'cfg'
files1 = os.path.join(os.path.abspath(os.curdir),"_" ,fi)
files1 = os.path.abspath(os.curdir) + "_" + fi
print(files1)

lstr = "cfg_5368778757.txt:cfg_5368778757.txt"

print(lstr.split(":")[0])

P1 = os.listdir("F:\\programming 2024\\Sci_Research\\testfolder")


delStr = "cfg_5368778762.txt:ABC"
print(P1)
P1.remove(delStr.split(":")[0])

print(len(P1))

