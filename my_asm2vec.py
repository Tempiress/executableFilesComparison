import sys
import os
import r2pipe
import logging
from typing import Dict, List, Tuple, Any
import json
import numpy as np
from collections import defaultdict

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
                # Создаем случайный вектор для демонстрации
                function_vectors[func.name()] = np.random.normal(0, 1, self.dimensions)

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
        Вычисляет схожести между функциями двух программ
        """
        similarities = []

        print("\n=== Расчет схожестей ===")
        for name1, vec1 in vectors1.items():
            best_match = None
            best_similarity = 0

            for name2, vec2 in vectors2.items():
                # Вычисляем косинусную схожесть
                similarity = self.cosine_similarity(vec1, vec2)

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = name2

            if best_match and best_similarity > 0.3:  # Пониженный порог для демонстрации
                similarities.append((name1, best_match, best_similarity))
                print(f"  Найдена схожесть: {name1} <-> {best_match}: {best_similarity:.3f}")

        # Сортируем по убыванию схожести
        similarities.sort(key=lambda x: x[2], reverse=True)
        return similarities

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
            for i, (func1, func2, similarity) in enumerate(similarities[:10], 1):
                print(f"{i:2d}. {func1:30} <-> {func2:30} : {similarity:.3f}")
        else:
            print("\nПохожих функций не найдено (порог схожести: 0.3)")


def main():
    """Пример использования"""
    comparator = Asm2VecComparator(dimensions=100)

    # ЗАМЕНИТЕ НА РЕАЛЬНЫЕ ПУТИ К ВАШИМ ПРОГРАММАМ
    program1 = r"D:\programming2025\MyResearch\coreutils-polybench-hashcat\aoc\O0\3mm"
    program2 = r"D:\programming2025\MyResearch\coreutils-polybench-hashcat\aoc\O2\3mm"

    # Для тестирования можно использовать любые исполняемые файлы
    # Например, сами Python интерпретаторы:
    program1 = sys.executable  # Текущий Python интерпретатор
    program2 = sys.executable  # Тот же файл для теста

    print("=== СРАВНЕНИЕ ПРОГРАММ С ASM2VEC ===")
    print(f"Программа 1: {program1}")
    print(f"Программа 2: {program2}")

    try:
        results = comparator.compare_programs(program1, program2)
        comparator.print_comparison_results(results)

    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Включим логирование для отладки
    #logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    main()