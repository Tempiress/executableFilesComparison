import sys
import os
import r2pipe
import logging
from typing import Dict, List, Tuple, Any, Set, Generator
import json
import numpy as np
from collections import defaultdict, deque
import pickle
import random
import datetime
from sklearn.model_selection import train_test_split

#from numba import njit
# Добавляем путь к asm2vec
ASM2VEC_PATH = r"D:\programming2025\asm2vecRework\MyResearch\asm2vec"
sys.path.append(ASM2VEC_PATH)

try:
    from asm2vec.asm import BasicBlock
    from asm2vec.asm import Function
    from asm2vec.asm import parse_instruction
    from asm2vec.model import Asm2Vec
    print("✓ asm2vec успешно импортирован!")
except Exception as e:
    print(f"Ошибка импорта asm2vec: {e}")


class CFGAnalyzer:
    """Анализатор для извлечения Control Flow Graph из исполняемых файлов"""
    
    def __init__(self):
        self.cfg_cache = {}
        self.call_graphs = {}

    def analyze_executable(self, exe_path: str) -> Dict[str, dict]:
        """Анализирует исполняемый файл и извлекает CFG для всех функций"""
        if exe_path in self.cfg_cache:
            return self.cfg_cache[exe_path]

        try:
            r2 = r2pipe.open(exe_path, flags=["-2", "-e io.cache=true"])
            r2.cmd("aaa")
            functions = r2.cmdj("aflj")

            if not functions:
                raise ValueError(f"No functions found in {exe_path}")

            cfg_data = {}
            for func in functions:
                func_name = func.get("name", f"unnamed_{func['addr']}")
                func_addr = func["addr"]

                r2.cmd(f"s {func_addr}")
                cfg_json = r2.cmdj("agj")

                cfg_data[func_name] = {
                    "addr": func_addr,
                    "cfg": cfg_json,
                    "name": func_name
                }

            return cfg_data

        except Exception as e:
            print(f"Error analyzing {exe_path}: {e}")
            raise
        finally:
            if 'r2' in locals():
                r2.quit()


class Asm2VecComparator:
    def __init__(self, dimensions: int = 200, model=None, 
                 num_random_walks: int = 10, 
                 num_epochs: int = 10):
        self.cfg_analyzer = CFGAnalyzer()


        
        if model is None:
            self.model = Asm2Vec(
                d=dimensions, 
                initial_alpha=0.025, 
                min_alpha=0.001, 
                jobs=20
            )
        else:
            self.model = model
        
        self.dimensions = dimensions
        self.num_epochs = num_epochs
        
        logging.basicConfig(level=logging.INFO)

    def extract_functions_for_asm2vec(self, cfg_data: dict) -> List[Function]:
        """
        Извлекает функции в формате, понятном для asm2vec
        """
        functions = []

        for func_name, func_data in cfg_data.items():
            try:
                cfg = func_data.get("cfg", {})
                blocks = cfg[0].get("blocks", [])

                if not blocks:
                    continue

                # Словарь: адрес блока -> объект BasicBlock
                bbs_dict = {}

                # Создаем все BasicBlock объекты
                for block in blocks:
                    block_addr = block["addr"]
                    basic_block = BasicBlock()

                    if 'ops' in block:
                        for op in block['ops']:
                            if 'opcode' in op:
                                instruction = op['opcode']
                                tokens = parse_instruction(instruction)
                                if tokens:
                                    basic_block.add_instruction(tokens)

                    bbs_dict[block_addr] = {
                        "block": basic_block,
                        "jump": block.get('jump', None),
                        "fail": block.get('fail', None)  # для условных переходов
                    }

                #Устанавливаем связи между блоками через add_successor
                for block_addr, bb_info in bbs_dict.items():
                    current_block = bb_info["block"]

                    # Добавляем переходы
                    if bb_info["jump"] is not None and bb_info["jump"] in bbs_dict:
                        current_block.add_successor(bbs_dict[bb_info["jump"]]["block"])

                    if bb_info["fail"] is not None and bb_info["fail"] in bbs_dict:
                        current_block.add_successor(bbs_dict[bb_info["fail"]]["block"])

                # Находим входной блок (первый блок в списке)
                # или блок с наименьшим адресом
                entry_block_addr = min(bbs_dict.keys())
                entry_block = bbs_dict[entry_block_addr]["block"]

                # Создание одного объекта Function с входным блоком
                func_obj = Function(entry_block, func_name)
                #functions.append(func_obj)
                yield func_obj

                #print(f"  Добавлена функция: {func_name} с {len(bbs_dict)} базовыми блоками")

            except Exception as e:
                logging.warning(f"Error processing function {func_name}: {e}")
                continue

    def train_model(self, list_programs: List[str]) -> 'Asm2Vec':
        """

        1. ВСЕ функции собираются в один репозиторий
        2. Обучение происходит num_epochs эпох на ВСЁМ репозитории
        3. Shuffle происходит перед каждой эпохой (внутри train())
        """
        print("=" * 70)
        print("НАЧАЛО ОБУЧЕНИЯ ASM2VEC")
        print("=" * 70)
        
        # 1. Собрать все функции из всех программ
        all_functions = []
        for program_path in list_programs:
            print(f"\n[1/3] Анализ программы: {program_path}")
            try:
                cfg = self.cfg_analyzer.analyze_executable(program_path)
                functions = list(self.extract_functions_for_asm2vec(cfg))
                all_functions.extend(functions)
                print(f"  ✓ Извлечено {len(functions)} функций из {program_path}")
            except Exception as e:
                print(f"  ✗ Ошибка при анализе {program_path}: {e}")
                continue

        if not all_functions:
            raise ValueError("Не удалось извлечь функции из программ")

        print(f"\n[2/3] Всего функций для обучения: {len(all_functions)}")
        #train_functions, val_functions = train_test_split(all_functions, test_size=0.2, random_state=42)
        # 2.
        print("[3/3] Создание репозитория и обучение модели...")
        #train_repo = self.model.make_function_repo(all_functions)

        # 3. Обучать num_epochs на всём репозитории
        print(f"\nОбучение {self.num_epochs} эпох на репозитории из {len(all_functions)} функций:")
        for epoch in range(self.num_epochs):
            print(f"  Эпоха {epoch + 1}/{self.num_epochs}...", end="", flush=True)

            #train_functions, val_functions = train_test_split(train_repo, test_size=0.2, random_state=42)

            self.model.train(all_functions)
            print(" ✓")

        print("\n" + "=" * 70)
        print("✓ ОБУЧЕНИЕ ЗАВЕРШЕНО")
        print("=" * 70)

        return self.model

    def vectorize_functions(self, functions: List[Function]) -> Dict[str, np.ndarray]:
        """
        Векторизует функции с помощью обученной модели.
        веса токенов фиксированы, обновляется только вектор функции.
        """
        if self.model is None:
            print("Модель не обучена!")
            return {}

        function_vectors = {}

        for func in functions:
            try:
                vector = self.model.to_vec(func)
                function_vectors[func.name()] = vector

                #print(f"  {func.name()}: norm={np.linalg.norm(vector):.4f}, "
                      #f"mean={vector.mean():.4f}, std={vector.std():.4f}")

            except Exception as e:
                logging.warning(f"Error vectorizing function {func.name()}: {e}")

        return function_vectors

    def train_model_sets(self, list_programs: List[str]):
        """Обучение на наборе программ """
        self.train_model(list_programs)
        return self.model

    def calculate_similarities(self, vectors1: Dict[str, np.ndarray],
                               vectors2: Dict[str, np.ndarray]) -> List[Tuple]:
        """Вычисляет схожести между функциями (уникальные пары)"""
        print("\n=== Расчет схожестей (уникальные пары) ===")

        all_possible_pairs = []
        for name1, vec1 in vectors1.items():
            for name2, vec2 in vectors2.items():
                #if name1 == name2 and np.array_equal(vec1, vec2):
                    #continue

                similarity = self.cosine_similarity(vec1, vec2)
                all_possible_pairs.append((name1, name2, similarity))

        all_possible_pairs.sort(key=lambda x: x[2], reverse=True)

        unique_similarities = []
        seen_func1 = set()
        seen_func2 = set()

        #for n1 in all_possible_pairs:
            #print(f"{n1[0]} <|-|> {n1[1]}: {n1[2]}")

        for name1, name2, similarity in all_possible_pairs:
            if name1 not in seen_func1 and name2 not in seen_func2:
                unique_similarities.append((name1, name2, similarity))
                seen_func1.add(name1)
                seen_func2.add(name2)

        return unique_similarities

    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Вычисляет косинусную схожесть между двумя векторами"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)


    def compare_with_pretrained_model(self, prog1_path: str, prog2_path: str):
        """Сравнение двух программ с предобученной моделью"""
        if not self.model:
            print("! Модель не загружена")
            return None

        print(f"\n=== Анализ программы 1: {prog1_path} ===")
        cfg1 = self.cfg_analyzer.analyze_executable(prog1_path)
        functions1 = list(self.extract_functions_for_asm2vec(cfg1))

        print(f"\n=== Анализ программы 2: {prog2_path} ===")
        cfg2 = self.cfg_analyzer.analyze_executable(prog2_path)
        functions2 = list(self.extract_functions_for_asm2vec(cfg2))

        print("\n=== Векторизация функций ===")
        vectors1 = self.vectorize_functions(functions1)
        vectors2 = self.vectorize_functions(functions2)

        print(f"Успешно векторизовано: {len(vectors1)} функций из prog1, "
              f"{len(vectors2)} из prog2")

        similarities = self.calculate_similarities(vectors1, vectors2)

        return {
            "prog1_vectors": vectors1,
            "prog2_vectors": vectors2,
            "similarities": similarities
        }

    def print_comparison_results(self, results: Dict):
        """Выводит результаты сравнения"""
        if not results:
            print("Нет результатов для вывода")
            return

        similarities = results['similarities']

        print("\n" + "=" * 50)
        print("РЕЗУЛЬТАТЫ СРАВНЕНИЯ ПРОГРАММ")
        print("=" * 50)
        print(f"Всего найдено {len(similarities)} пар похожих функций")
        print(f"Функций в программе 1: {len(results['prog1_vectors'])}")
        print(f"Функций в программе 2: {len(results['prog2_vectors'])}")

        k = 0

        if similarities:
            for i, (func1, func2, similarity) in enumerate(similarities[:], 1):
                if func1 == func2:
                    k+=1
                print(f"{i:2d}. {func1:30} <-> {func2:30} : {similarity:.3f}")
        else:
            print("\nПохожих функций не найдено")

        print(f"count of sim = {k / len(similarities)}")


    def save_model(self, filepath: str):
        """Сохраняет обученную модель"""
        if self.model is None:
            print("Нет обученной модели для сохранения")
            return

        with open(filepath, "wb") as f:
            pickle.dump(self.model, f)
        print(f"Модель сохранена в {filepath}")

    def load_model(self, filepath: str):
        """Загружает обученную модель"""
        with open(filepath, "rb") as f:
            self.model = pickle.load(f)
        print("Модель успешно загружена")


def main():
    SEED = 42
    random.seed(SEED)
    np.random.seed(SEED)


    comparator = Asm2VecComparator(
        dimensions=200,      # Примерно 200
        num_random_walks=10,  # 10 random walks для функции
        num_epochs=1         # примерно 10
    )

    program1 = r"D:\programming2025\MyResearch\coreutils-polybench-hashcat\aoc\O0\3mm"
    program2 = r"D:\programming2025\MyResearch\coreutils-polybench-hashcat\aoc\O2\3mm"
    program3 = r"D:\programming2025\MyResearch\coreutils-polybench-hashcat\aoc\O2\chroot"
    program4 = r"D:\programming2025\MyResearch\coreutils-polybench-hashcat\aoc\O2\covariance"
    program5 = r"D:\programming2025\MyResearch\coreutils-polybench-hashcat\aoc\O2\expr"
    program6 = r"D:\programming2025\MyResearch\coreutils-polybench-hashcat\aoc\Os\chroot"
    program7 = r"D:\programming2025\MyResearch\coreutils-polybench-hashcat\aoc\O6\chroot"
    program8 = r"D:\programming2025\MyResearch\coreutils-polybench-hashcat\aoc\O2\chroot"
    program100 = r"D:\programming2025\MyResearch\train_programs\elevator.exe"

    folder_path = "./train_programs"
    # list_programs = [
    #     os.path.join(folder_path, f)
    #     for f in os.listdir(folder_path)
    #     if os.path.isfile(os.path.join(folder_path, f))
    # ]

    list_programs = []
    list_programs.append(program1)
    list_programs.append(program2)
    list_programs.append(program4)
    #list_programs.append(program5)
    #list_programs.append(program6)
    #list_programs.append(program7)
    #list_programs.append(program8)

    print(f"Программы для обучения: {list_programs}")

    try:
        start = datetime.datetime.now()
        # Обучение на репозитории
        trained_model = comparator.train_model(list_programs)

        # Сохранение обученной модели
        comparator.save_model("./asm2vec2_model.pkl")
        # comparator.load_model("./asm2vec_model.pkl")
        # Сравнение программ
        sim = comparator.compare_with_pretrained_model(program4, program4)
        comparator.print_comparison_results(sim)

        finish = datetime.datetime.now()
        print('Время работы: ' + str(finish - start))

    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
