import logging
import os
import pickle
import sys
from typing import Dict, List, Tuple

import numpy as np
import r2pipe

# Добавляем путь к asm2vec
ASM2VEC_PATH = r"D:\programming2025\MyResearch\asm2vec"
sys.path.append(ASM2VEC_PATH)

try:
    # Импортируем из правильных модулей
    from asm2vec.asm import BasicBlock
    from asm2vec.asm import Function
    from asm2vec.asm import parse_instruction
    from asm2vec.model import Asm2Vec
    #from asm2vec.asm import parse_instruction

    print("✓ asm2vec успешно импортирован!")
except :
    print("error")

class CFGAnalyzer:
    def __init__(self):
        self.cfg_cache = {}
        self.call_graphs = {}

    def analyze_executable(self, exe_dist: str) -> Dict[str, dict]:
        if exe_dist in self.cfg_cache:
            return self.cfg_cache[exe_dist]

        try:
            r2 = r2pipe.open(exe_dist, flags=["-2", "-e io.cache=true"])
            r2.cmd("aaa")
            functions = r2.cmdj("aflj")

            if not functions:
                raise ValueError(f"No functions found in {exe_dist}")

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
            #q = json.dumps(cfg_data)

            #self.cfg_cache[exe_dist] = cfg_data
            return cfg_data

        except Exception as e:
            print(f"Error analyzing {exe_dist}: {e}")
            raise
        finally:
            if 'r2' in locals():
                r2.quit()


class Asm2VecComparator:
    def __init__(self, dimensions=200, model = None):
        self.cfg_analyzer = CFGAnalyzer()
        if model is None:
            self.model = Asm2Vec(d=dimensions, initial_alpha=0.025, min_alpha=0.001, jobs=20)
        else:
            self.model = model
        self.dimensions = dimensions


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

        #return functions

    def train_model(self, list_programs: List[Function]):
        # Собрать все функции из всех программ
        all_functions = []
        for program in list_programs:
            cfg = self.cfg_analyzer.analyze_executable(program)
            functions = list(self.extract_functions_for_asm2vec(cfg))
            all_functions.extend(functions)

        print(f"Всего функций для обучения: {len(all_functions)}")


        train_repo = self.model.make_function_repo(all_functions)


        #for epoch in range(1):
            #print(f"Эпоха {epoch + 1}/5")
        self.model.train(train_repo)

        return self.model

    def vectorize_functions(self, functions: List[Function]) -> Dict[str, np.ndarray]:
        """
        Векторизует функции с помощью обученной модели
        """
        if self.model is None:
            print("Модель не обучена!")
            return

        function_vectors = {}

        for func in functions:
            try:
                # Получаем вектор функции
                vector = self.model.to_vec(func)
                vector2 = self.model.to_vec(func)
                function_vectors[func.name()] = vector

                # Логируем статистику для отладки
                print(f"  {func.name()}: norm={np.linalg.norm(vector):.4f}, "
                      f"mean={vector.mean():.4f}, std={vector.std():.4f}")

                #print(f"  Векторизована: {func.name()}")

            except Exception as e:
                logging.warning(f"Error vectorizing function {func.name()}: {e}")

        return function_vectors



    def train_model_sets(self, list_programs):
        """
        Обучение модели
        """
        self.train_model([list_programs])
        #p = []
        # for progr in list_programs:
        #     cfg1 = self.cfg_analyzer.analyze_executable(progr)
            #p = p + self.extract_functions_for_asm2vec(cfg1)
            #print(f"Всего функций для обучения: {len(self.extract_functions_for_asm2vec(cfg1))}")
            # for func in self.extract_functions_for_asm2vec(cfg1):
            #     self.train_model([func])

        #print(f"Всего функций для обучения: {len(p)}")

        #if len(p) < 2:
            #print("Недостаточно функций для анализа!")
            #return None

        # Обучаем модель
        #self.train_model(p)
        return self.model


    def calculate_similarities(self, vectors1: Dict[str, np.ndarray],
                               vectors2: Dict[str, np.ndarray]) -> List[Tuple]:
        """
        Вычисляет схожести между функциями двух программ, формируя уникальные пары
        с наилучшей взаимной схожестью.
        """
        print("\n=== Расчет схожестей (уникальные пары) ===")

        # 1. Находим все возможные пары между функциями двух программ,
        #    превышающие порог схожести.
        all_possible_pairs = []
        for name1, vec1 in vectors1.items():
            for name2, vec2 in vectors2.items():
                # Если сравниваются два одинаковых файла, можно пропустить сравнение функции с самой собой
                #if name1 == name2:#np.array_equal(vec1, vec2):
                    #similarity = self.cosine_similarity(vec1, vec2)
                    #continue


                similarity = self.cosine_similarity(vec1, vec2)

                # Сохраняем все пары с результатом выше порога
                #if similarity > 0:
                all_possible_pairs.append((name1, name2, similarity))

        # 2. Сортируем все найденные пары по убыванию коэффициента схожести.
        #    Таким образом, самые похожие пары будут в начале списка.
        all_possible_pairs.sort(key=lambda x: x[2], reverse=True)

        #3. "Жадно" выбираем лучшие уникальные пары.
        #   Проходим по отсортированному списку и добавляем пару, только если
        #   ни одна из функций в ней еще не была использована.
        unique_similarities = []
        seen_func1 = set()
        seen_func2 = set()

        for name1, name2, similarity in all_possible_pairs:
            # Проверяем, что обе функции еще "свободны"
            if name1 not in seen_func1 and name2 not in seen_func2:
                # Если да, добавляем эту пару в итоговый результат
                unique_similarities.append((name1, name2, similarity))

                # И помечаем обе функции как "занятые"
                seen_func1.add(name1)
                seen_func2.add(name2)

                #print(f" Найдена уникальная пара: {name1} <-> {name2}: {similarity:.3f}")

        # Финальная сортировка не требуется, так как мы уже обработали отсортированный список,
        # но для наглядности в выводе можно оставить.
        return unique_similarities

    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Вычисляет косинусную схожесть между двумя векторами"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

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

        if similarities:
            #print("\nТОП-10 самых похожих функций:")
            #print("-" * 60)
            for i, (func1, func2, similarity) in enumerate(similarities[:], 1):
                print(f"{i:2d}. {func1:30} <-> {func2:30} : {similarity:.3f}")
        else:
            print("\nПохожих функций не найдено (порог схожести: 0.3)")

    def compare_with_trained_model(self, query_program):
        """Сравнение новой программы с обученной моделью"""
        # 1. Извлечь функции из query (НЕ из репозитория!)
        cfg = self.cfg_analyzer.analyze_executable(query_program)
        query_functions = list(self.extract_functions_for_asm2vec(cfg))

        # 2. Estimate векторов (веса модели фиксированы)
        query_vectors = self.vectorize_functions(query_functions)

        return query_vectors

    def compare_with_pretrained_model(self, prog1_path: str, prog2_path: str):
        if not self.model:
            print("! Модель не загружена")
            return None

        # 1) Анализируем и извлекаем функции
        cfg1 = self.cfg_analyzer.analyze_executable(prog1_path)
        functions1 = self.extract_functions_for_asm2vec(cfg1)

        cfg2 = self.cfg_analyzer.analyze_executable(prog2_path)
        functions2 = self.extract_functions_for_asm2vec(cfg2)

        # 2) Сразу векторизуем, используя загруженную модель
        # Обучение (train_model) пропускается
        print("Векторизация функций с использованием предобученной модели...")
        vectors1 = self.vectorize_functions(functions1)
        vectors2 = self.vectorize_functions(functions2)

        # Шаг 3: Считаем схожесть
        similarities = self.calculate_similarities(vectors1, vectors2)

        return {
            "prog1_vectors": vectors1,
            "prog2_vectors": vectors2,
            "similarities": similarities
        }

    def get_similar(self, p1, p2):

        print(f"\n=== Анализ программы 1: {p1} ===")
        cfg1 = self.cfg_analyzer.analyze_executable(p1)
        functions1 = self.extract_functions_for_asm2vec(cfg1)

        print(f"\n=== Анализ программы 2: {p2} ===")
        cfg2 = self.cfg_analyzer.analyze_executable(p2)
        functions2 = self.extract_functions_for_asm2vec(cfg2)

        # Векторизуем функции
        print("\n=== Векторизация функций ===")
        vectors1 = self.vectorize_functions(functions1)
        vectors2 = self.vectorize_functions(functions2)

        print(f"Успешно векторизовано: {len(vectors1)} функций из prog1, {len(vectors2)} из prog2")

        # Сравниваем функции
        similarities = self.calculate_similarities(vectors1, vectors2)

        return {
            'prog1_vectors': vectors1,
            'prog2_vectors': vectors2,
            'similarities': similarities
        }

    def save_model(self, filepath:str):
        if self.model is None:
            print("Нет обученной модели для сохранения")
            return

        with open(filepath, "wb") as f:
            pickle.dump(self.model, f)
        print(f"Модель сохранена в  {filepath}")

    def load_model(self, filepath: str):
        with open(filepath, "rb") as f:
            self.model = pickle.load(f)
        print("Модель успешно загружена")




def main():
    comparator = Asm2VecComparator(dimensions=200)

    program1 = r"D:\programming2025\MyResearch\coreutils-polybench-hashcat\aoc\O0\3mm"
    program2 = r"D:\programming2025\MyResearch\coreutils-polybench-hashcat\aoc\O2\3mm"
    program3 = r"D:\programming2025\MyResearch\coreutils-polybench-hashcat\aoc\O3\3mm"
    program4 = r"D:\programming2025\MyResearch\train_programs\Dism++x64.exe"

    # print("=== СРАВНЕНИЕ ПРОГРАММ С ASM2VEC ===")
    folder_path = "./train_programs"
    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    #list_programs = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    #list_programs = list_programs#[7:10]
    list_programs = []
    list_programs.append(program1)
    #list_programs.append(program1)
    print(list_programs)
    #list_programs.append(program1)
    #list_programs.append(program2)
    #list_programs.append(program3)

    try:
        # ========================Test 1=======================================
        # trained_model = comparator.train_model_sets(list_programs)
        # sim = comparator.compare_with_pretrained_model(program1, program1)
        # comparator.print_comparison_results(sim)
        # trained_model2 = comparator.train_model_sets(list_programs)
        # trained_model3 = comparator.train_model_sets(list_programs)
        # #comparator.save_model("./mm")
        # #comparator.load_model("./mm")
        # sim2 = comparator.compare_with_pretrained_model(program1, program1)
        # comparator.print_comparison_results(sim2)
        # =====================================================================
        # ========================Test 2=======================================
        trained_model_0 = comparator.train_model(list_programs) # train_model_sets(list_programs)

        comparator.save_model("./mm_0300")
        #comparator.load_model("./mm_0")
        sim = comparator.compare_with_pretrained_model(program3, program3)
        comparator.print_comparison_results(sim)

        # for i in range(20):
        #     trained_model_ = comparator.train_model_sets(list_programs)
        # sim_2 = comparator.compare_with_pretrained_model(program1, program1)
        # comparator.print_comparison_results(sim_2)




    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()