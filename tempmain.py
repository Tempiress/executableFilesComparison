# for file in filenames:
#     for dirindex1 in range(0, len(l1)):
#         l2 = os.listdir(f'./coreutils-polybench-hashcat/{l1[dirindex1]}')  # O0 O1 O2
#         print("len:" + str(len(l1)))
#         for dirindex2 in range(1, len(l2)):
#             # spinner.next()
#             aq = f'./coreutils-polybench-hashcat/{l1[dirindex1]}/{l2[0]}/{file}'
#             bq = f'./coreutils-polybench-hashcat/{l1[dirindex1]}/{l2[dirindex2]}/{file}'
#             q = asyncio.run(run(aq, bq))
#             # print(f'./coreutils-polybench-hashcat/{l1[dirindex1]}/{l2[0]}/{file};./coreutils-polybench-hashcat/{l1[dirindex1]}/{l2[dirindex2]}/{file};{str(round(q, 4))}\n')
#             f.write(f'./coreutils-polybench-hashcat/{l1[dirindex1]}/{l2[0]}/{file};./coreutils-polybench-hashcat/{l1[dirindex1]}/{l2[dirindex2]}/{file};{str(round(q, 4))}\n')
#
#     # bar2.next()
# # bar2.finish()
# # spinner.finish()
# f.close()






# start_time = time.time()
# for file in filenames:
#     for dirindex1 in range(0, len(l1)):
#         l2 = os.listdir(f'./coreutils-polybench-hashcat/{l1[dirindex1]}')  # O0 O1 O2
#         print("len:" + str(len(l1)))
#         for dirindex2 in range(1, len(l2)):
#             # spinner.next()
#             aq = f'./coreutils-polybench-hashcat/{l1[dirindex1]}/{l2[0]}/{file}'
#             bq = f'./coreutils-polybench-hashcat/{l1[dirindex1]}/{l2[dirindex2]}/{file}'
#             q = asyncio.run(run(aq, bq))
#             # print(f'./coreutils-polybench-hashcat/{l1[dirindex1]}/{l2[0]}/{file};./coreutils-polybench-hashcat/{l1[dirindex1]}/{l2[dirindex2]}/{file};{str(round(q, 4))}\n')
#             f.write(f'./coreutils-polybench-hashcat/{l1[dirindex1]}/{l2[0]}/{file};./coreutils-polybench-hashcat/{l1[dirindex1]}/{l2[dirindex2]}/{file};{str(round(q, 4))}\n')
#
# f.close()
# end_time = time.time()
# execution_time = end_time - start_time
# print(f"Time to working: {execution_time} seconds")
# print(l1)





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