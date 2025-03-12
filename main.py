import os

from run import run


# q = run(".\\coreutils-polybench-hashcat\\c09\\O0\\cap2hccapx", ".\\coreutils-polybench-hashcat\\c09\\O0\\ct3_to_ntlm")
# print("Result:", round(q, 4))

# f = open("./Debugging./avedick.txt", mode='a')
# f.write("Abc\n")
# f.write("Porasd\n")
# f.close()

# Берём один файл и сравниваем его все виды
fileName = "adi"

l1 = os.listdir('./coreutils-polybench-hashcat/')  # aoc, c07, c06
# print(l1[])
f = open("./Debugging./avedick.txt", mode='a')
for dirindex1 in range(0, len(l1)):
    l2 = os.listdir(f'./coreutils-polybench-hashcat/{l1[dirindex1]}')  # O0 O1 O2
    for dirindex2 in range(1, len(l2)):
        q = run(f'./coreutils-polybench-hashcat/{l1[dirindex1]}/{l2[0]}/{fileName}', f'./coreutils-polybench-hashcat/{l1[dirindex1]}/{l2[dirindex2]}/{fileName}')
        print(f'./coreutils-polybench-hashcat/{l1[dirindex1]}/{l2[0]}/{fileName}' + f'./coreutils-polybench-hashcat/{l1[dirindex1]}/{l2[dirindex2]}/{fileName}'
              + str(q))

        f.write(f'./coreutils-polybench-hashcat/{l1[dirindex1]}/{l2[0]}/{fileName} ' + f'&& ./coreutils-polybench-hashcat/{l1[dirindex1]}/{l2[dirindex2]}/{fileName} '
                + '-> ' + str(round(q, 4)) + '\n' + '--------' + ' \n')
f.close()


