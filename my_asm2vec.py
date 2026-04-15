import logging
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
    from asm2vec.asm import parse_instruction

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

            self.cfg_cache[exe_dist] = cfg_data
            return cfg_data

        except Exception as e:
            print(f"Error analyzing {exe_dist}: {e}")
            raise
        finally:
            if 'r2' in locals():
                r2.quit()


class Asm2VecComparator:
    def __init__(self, dimensions=200):
        self.cfg_analyzer = CFGAnalyzer()
        self.model = None
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

                # Собираем все инструкции функции
                # all_instructions = []
                all_instructions = BasicBlock()
                for block in blocks:
                    # block_ = BasicBlock()
                    if 'ops' in block:
                        for op in block['ops']:
                            if 'opcode' in op:
                                instruction = op['opcode']
                                # tokens = self.parse_instruction_tokens(instruction)
                                tokens = parse_instruction(instruction)
                                if tokens:
                                    # all_instructions.append(tokens)
                                    all_instructions.add_instruction(tokens)

                if all_instructions:
                    # Создаем объект функции для asm2vec
                    func_obj = Function(all_instructions, func_name)
                    functions.append(func_obj)
                    print(f"  Добавлена функция: {func_name} с {len(all_instructions)} инструкциями")

            except Exception as e:
                logging.warning(f"Error processing function {func_name}: {e}")
                continue

        return functions

    def train_model(self, functions: List[Function]):
        """
        Обучает модель asm2vec на предоставленных функциях
        """
        if len(functions) < 2:
            print("Недостаточно функций для обучения (нужно минимум 2)")
            return

        print(f"Обучение модели на {len(functions)} функциях...")

        try:
            # Создаем модель
            self.model = Asm2Vec(d=self.dimensions, initial_alpha=0.025, min_alpha=0.001, jobs=5000)
            train_repo = self.model.make_function_repo(functions)
            # Обучаем модель
            print("Начало обучения...")
            self.model.train(train_repo)
            print("Модель обучена!")
            return self.model

        except Exception as e:
            print(f"Ошибка при обучении модели: {e}")
            import traceback
            traceback.print_exc()


    def vectorize_functions(self, functions: List[Function]) -> Dict[str, np.ndarray]:
        """
        Векторизует функции с помощью обученной модели
        """
        if self.model is None:
            print("Модель не обучена!")
            return #self._create_dummy_vectors(functions)

        function_vectors = {}

        for func in functions:
            try:
                # Получаем вектор функции
                vector = self.model.to_vec(func)
                function_vectors[func.name()] = vector
                print(f"  Векторизована: {func.name()}")

            except Exception as e:
                logging.warning(f"Error vectorizing function {func.name()}: {e}")

        return function_vectors



    def compare_programs(self, prog1_path: str, prog2_path: str):
        """
        Сравнивает две программы используя asm2vec
        """
        print(f"\n=== Анализ программы 1: {prog1_path} ===")
        cfg1 = self.cfg_analyzer.analyze_executable(prog1_path)
        functions1 = self.extract_functions_for_asm2vec(cfg1)


        print(f"\n=== Анализ программы 2: {prog2_path} ===")
        cfg2 = self.cfg_analyzer.analyze_executable(prog2_path)
        functions2 = self.extract_functions_for_asm2vec(cfg2)

        print(f"\nНайдено функций: prog1 - {len(functions1)}, prog2 - {len(functions2)}")

        # Объединяем функции для обучения
        all_functions = functions1 + functions2
        print(f"Всего функций для обучения: {len(all_functions)}")

        if len(all_functions) < 2:
            print("Недостаточно функций для анализа!")
            return None

        # Обучаем модель
        self.train_model(all_functions)

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
                if name1 == name2 and np.array_equal(vec1, vec2):
                    continue

                similarity = self.cosine_similarity(vec1, vec2)

                # Сохраняем все пары с результатом выше порога
                #if similarity > 0.3:
                all_possible_pairs.append((name1, name2, similarity))

        # 2. Сортируем все найденные пары по убыванию коэффициента схожести.
        #    Таким образом, самые похожие пары будут в начале списка.
        all_possible_pairs.sort(key=lambda x: x[2], reverse=True)

        # 3. "Жадно" выбираем лучшие уникальные пары.
        #    Проходим по отсортированному списку и добавляем пару, только если
        #    ни одна из функций в ней еще не была использована.
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

                print(f" Найдена уникальная пара: {name1} <-> {name2}: {similarity:.3f}")

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
            print("\nТОП-10 самых похожих функций:")
            print("-" * 60)
            for i, (func1, func2, similarity) in enumerate(similarities[:], 1):
                print(f"{i:2d}. {func1:30} <-> {func2:30} : {similarity:.3f}")
        else:
            print("\nПохожих функций не найдено (порог схожести: 0.3)")

    def save_model(self, path: str):
        if self.model:
            print(f"Сохранение модели в {path}")
            self.model.save(path)
        else:
            print("Модель не обучена, нечего сохранять.")

    def load_model(self, path: str):
        print(f"Загрузка модели из {path}")
        self.model = Asm2Vec.load(path)
        self.dimensions = self.model.d


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


def main():

    comparator = Asm2VecComparator(dimensions=100)

    program1 = r"D:\programming2025\MyResearch\coreutils-polybench-hashcat\aoc\O0\3mm"
    program2 = r"D:\programming2025\MyResearch\coreutils-polybench-hashcat\aoc\O2\3mm"


    #program1 = sys.executable  # Текущий Python интерпретатор
    #program2 = sys.executable  # Тот же файл для теста

    print("=== СРАВНЕНИЕ ПРОГРАММ С ASM2VEC ===")
    print(f"Программа 1: {program1}")
    print(f"Программа 2: {program2}")

    try:
        results = comparator.compare_programs(program1, program2)
        comparator.save_model("./")
        comparator.print_comparison_results(results)

    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # логирование для отладки
    #logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    main()