import logging
import time
from typing import Dict

import r2pipe


class CFGAnalyzer:
    def __init__(self):
        self.cfg_cache = {}  # Кэш для хранения CFG в памяти
        self.call_graphs = {}  # Кэш для графов вызовов

    def analyze_executable(self, exe_dist: str) -> Dict[str, dict]:
        """
        Анализирует исполняемый файл и возвращает CFG в памяти
        :param exe_dist: Путь к исполняемому файлу
        :return: Словарь с CFG {имя_функции: cfg_data}
        """
        if exe_dist in self.cfg_cache:
            return self.cfg_cache[exe_dist]

        try:
            # Открываем бинарник
            r2 = r2pipe.open(exe_dist, flags=["-2", "-e io.cache=true"])

            # Выполняем анализ (асинхронно)
            r2.cmd("aaa")

            # Получаем список функций
            functions = r2.cmdj("aflj")

            if not functions:
                raise ValueError(f"No functions found in {exe_dist}")

            cfg_data = {}

            # Анализируем каждую функцию
            for func in functions:
                func_name = func.get("name", f"unnamed_{func['addr']}")
                func_addr = func["addr"]


                if func.get("nbbs", 0) < 2:
                    #cfg_json2 = r2.cmdj(f"agj {func_addr}")
                    continue

                # Получаем CFG для функции
                # r2.cmd(f"agf @ {func_addr}")
                cfg_json = r2.cmdj(f"agj {func_addr}")

                cfg_data[func_name] = {
                    "addr": func_addr,
                    "cfg": cfg_json,
                    "name": func_name
                }

            # Сохраняем в кэш
            self.cfg_cache[exe_dist] = cfg_data
            return cfg_data

        except Exception as e:
            logging.error(f"Error analyzing {exe_dist}: {e}")
            with open(f"error_log{time.time()}.txt", "a") as f:
                f.write(f"Error analyzing {exe_dist}: {e}\n")
            raise
        finally:
            if 'r2' in locals():
                r2.quit()

    def get_call_graph(self, exe_dist: str) -> dict:
        """
        Получает граф вызовов и сохраняет в памяти
        :param exe_dist: Путь к исполняемому файлу
        :return: Граф вызовов в виде словаря
        """
        if exe_dist in self.call_graphs:
            return self.call_graphs[exe_dist]

        try:
            r2 = r2pipe.open(exe_dist, flags=["-2", "-e io.cache=true"])
            r2.cmd("aaa")

            # Получаем граф вызовов
            call_graph =r2.cmdj("agCj")

            #with open("debug_json.json", "w") as f:
             #   json.dump(call_graph, f)

            self.call_graphs[exe_dist] = call_graph
            return call_graph

        except Exception as e:
            logging.error(f"Error getting call graph for {exe_dist}: {e}")
            with open(f"error_log{time.time()}.txt", "a") as f:
                f.write(f"Error analyzing {exe_dist}: {e}\n")
            raise
        finally:
            if 'r2' in locals():
                r2.quit()

