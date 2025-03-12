import json
import os
import random
from run import run

def generateCompare(count):
    visited_similar = {}
    visited_different = {}
    PATH = os.getcwd()
    worked_directory = os.path.join(PATH, 'coreutils-polybench-hashcat')

    if not os.path.exists(worked_directory):
        print("Папки нет!")
        return

    # Список папок в рабочей директории(aoc, c07, ...)
    dirs_level1 = os.listdir(worked_directory)
    cnt_similar = 1
    cnt_different = 1

    # Пары похожих Программ
    for i in range(int(count)):
        while True:
            # Выбор двух разных папок 1 - го уровня
            dir1_index, dir2_index = random.sample(range(len(dirs_level1)), 2)
            path_dir1 = os.path.join(worked_directory, dirs_level1[dir1_index])
            path_dir2 = os.path.join(worked_directory, dirs_level1[dir2_index])

            dirs_level2_1 = os.listdir(path_dir1)
            dirs_level2_2 = os.listdir(path_dir2)

            dir2_1_index = random.randint(0, len(dirs_level2_1) - 1)
            dir2_2_index = random.randint(0, len(dirs_level2_2) - 1)

            path_dir3_1 = os.path.join(path_dir1, dirs_level2_1[dir2_1_index])
            path_dir3_2 = os.path.join(path_dir2, dirs_level2_2[dir2_2_index])

            dirs_level3_1 = os.listdir(path_dir3_1)
            dirs_level3_2 = os.listdir(path_dir3_2)

            # Выбор случайных файлов (уровень 3)
            file1 = random.choice(dirs_level3_1)
            file2 = random.choice(dirs_level3_2)

            if file1 == file2:
                path_file1 = os.path.join(path_dir3_1, file1)
                path_file2 = os.path.join(path_dir3_2, file2)
                if path_file1 not in visited_similar.values():
                    visited_similar[cnt_similar] = (path_file1, path_file2)
                    cnt_similar += 1
                    break

    # Пары непохожих программ
    for i in range(int(count)):
        while True:
            # Выбор двух разных папок 1-го уровня
            dir1_index, dir2_index = random.sample(range(len(dirs_level1)), 2)
            path_dir1 = os.path.join(worked_directory, dirs_level1[dir1_index])
            path_dir2 = os.path.join(worked_directory, dirs_level1[dir2_index])

            dirs_level2_1 = os.listdir(path_dir1)
            dirs_level2_2 = os.listdir(path_dir2)

            # Выбор случайных папок 2-го уровня
            dir2_1_index = random.randint(0, len(dirs_level2_1) - 1)
            dir2_2_index = random.randint(0, len(dirs_level2_2) - 1)

            path_dir3_1 = os.path.join(path_dir1, dirs_level2_1[dir2_1_index])
            path_dir3_2 = os.path.join(path_dir2, dirs_level2_2[dir2_2_index])

            dirs_level3_1 = os.listdir(path_dir3_1)
            dirs_level3_2 = os.listdir(path_dir3_2)

            # Выбор случайных файлов (уровень 3)
            file1 = random.choice(dirs_level3_1)
            file2 = random.choice(dirs_level3_2)

            if file1 != file2:
                path_file1 = os.path.join(path_dir3_1, file1)
                path_file2 = os.path.join(path_dir3_2, file2)
                if path_file1 not in visited_different.values():
                    visited_different[cnt_different] = (path_file1, path_file2)
                    cnt_different += 1
                    break
    with open("./pairsComparison/similar_pairs.json", "w") as f_sim:
        print(json.dumps(visited_similar))
        f_sim.write(json.dumps(visited_similar))

    with open("./pairsComparison/different_pairs.json", "w") as f_dif:
        f_dif.write(json.dumps(visited_different))
    print("Пары похожих:")
    for i, v in visited_similar.items():
        print(str(i) + " " + v[0] + "----и----" + v[1])

    for k, m in visited_different.items():
        print(str(k) + " " + m[0] + "----и----" + m[1])



def JsonHemmingPair(file, name_of_path):
    paris = {}


    with open(file, "r") as f:
        file_parse = json.load(f)

    print("________________________")
    print(file_parse)

    for index, comparis in file_parse.items():
        hem = run(comparis[0], comparis[1])
        paris[index] = {"hemming": hem,
                        "p1": comparis[0],
                        "p2": comparis[1]
                        }


    print("--------------")
    print(name_of_path)
    with open(name_of_path, "w") as compf:
        compf.write(json.dumps(paris))


# count = input("enter count of comparisons: ")
# generateCompare(count)

# JsonHemmingPair(".\pairsComparison\similar_pairs.json", ".\pairsComparison\sim_p_with_hemming.json")
# JsonHemmingPair(".\pairsComparison\different_pairs.json", ".\pairsComparison\diff_p_with_hemming.json")
# q = run(".\\coreutils-polybench-hashcat\\aoc\\O0\\covariance", ".\\coreutils-polybench-hashcat\\aoc\\O0\\combinator")
# q = run(".\\coreutils-polybench-hashcat\\c07\\O0\\bicg", ".\\coreutils-polybench-hashcat\\c07\\O0\\dirname")
# q = run(".\\coreutils-polybench-hashcat\\aoc\\O0\\cutb", ".\\coreutils-polybench-hashcat\\aoc\\O2\\cutb")
q = run(".\\coreutils-polybench-hashcat\\c09\\O0\\cap2hccapx", ".\\coreutils-polybench-hashcat\\c09\\O0\\ct3_to_ntlm")
# q = run(".\\coreutils-polybench-hashcat\\aoc\O0\\expander", ".\\coreutils-polybench-hashcat\\c08\\O2\\chmod")
# q = run("HW3.exe", ".\\HW8.exe")
# хеши от 0 до 1
print("Result:", round(q, 4))