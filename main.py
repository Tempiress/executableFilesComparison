import datetime
import os
from progress.bar import Bar
from run import run

# q = run(".\\coreutils-polybench-hashcat\\c09\\O0\\cap2hccapx", ".\\coreutils-polybench-hashcat\\c09\\O0\\ct3_to_ntlm")
# print("Result:", round(q, 4))
#
# f = open("./Debugging./avedick.txt", mode='a')
# f.write("Abc\n")
# f.write("Porasd\n")
# f.close()

# Берём один файл и сравниваем его все виды
fileName = "3mm"
filenames = os.listdir('./coreutils-polybench-hashcat/aoc/Os/')
filenames.remove('2mm')
l1 = os.listdir('./coreutils-polybench-hashcat/')  # aoc, c07, c06
# print(l1[])
bar2 = Bar('Processing2', max=len(filenames))
f = open(f"./Debugging./dbg{str(datetime.datetime.now().hour)}{datetime.datetime.now().minute}.txt", mode='a')
for file in filenames:
    for dirindex1 in range(0, len(l1)):
        l2 = os.listdir(f'./coreutils-polybench-hashcat/{l1[dirindex1]}')  # O0 O1 O2
        print("len:" + str(len(l1)))
        for dirindex2 in range(1, len(l2)):
            aq = f'./coreutils-polybench-hashcat/{l1[dirindex1]}/{l2[0]}/{file}'
            bq = f'./coreutils-polybench-hashcat/{l1[dirindex1]}/{l2[dirindex2]}/{file}'
            q = run(aq, bq)
            print(f'./coreutils-polybench-hashcat/{l1[dirindex1]}/{l2[0]}/{file}' + f'./coreutils-polybench-hashcat/{l1[dirindex1]}/{l2[dirindex2]}/{file} '
                  + str(q))

            f.write(f'./coreutils-polybench-hashcat/{l1[dirindex1]}/{l2[0]}/{file} ' + f'&& ./coreutils-polybench-hashcat/{l1[dirindex1]}/{l2[dirindex2]}/{file} '
                    + '-> ' + str(round(q, 4)) + '\n' + '--------' + ' \n')
    bar2.next()
bar2.finish()
f.close()




# filenames = os.listdir('./coreutils-polybench-hashcat/aoc/Os/')
# filenames.remove('2mm')
# l1 = os.listdir('./coreutils-polybench-hashcat/')  # aoc, c07, c06
# # print(l1[])
#
# f = open(f"./Debugging./dbg{str(datetime.datetime.now().hour)}{datetime.datetime.now().minute}.txt", mode='a')
# for fileindex in range(1, len(filenames)):
#     for dirindex1 in range(0, len(l1)):
#         l2 = os.listdir(f'./coreutils-polybench-hashcat/{l1[dirindex1]}')  # O0 O1 O2
#         print("len:" + str(len(l1)))
#         for dirindex2 in range(1, len(l2)):
#             aq = f'./coreutils-polybench-hashcat/{l1[dirindex1]}/{l2[dirindex2]}/{filenames[fileindex]}'
#             bq = f'./coreutils-polybench-hashcat/{l1[dirindex1]}/{l2[dirindex2]}/{filenames[fileindex + 1]}'
#             q = run(aq, bq)
#
#             f.write(f'./coreutils-polybench-hashcat/{l1[dirindex1]}/{l2[0]}/{filenames[fileindex]} ' + f'&& ./coreutils-polybench-hashcat/{l1[dirindex1]}/{l2[dirindex2]}/{filenames[fileindex + 1]} '
#                     + '-> ' + str(round(q, 4)) + '\n' + '--------' + ' \n')
#
# f.close()


