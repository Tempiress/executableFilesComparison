import r2pipe
import logging
import asyncio
from typing import Dict, List, Tuple
import json


class CFGAnalyzer:
    def __init__(self):
        self.cfg_cache = {}  # Кэш для хранения CFG в памяти
        self.call_graphs = {}  # Кэш для графов вызовов

    async def analyze_executable(self, exe_dist: str) -> Dict[str, dict]:
        """
        Анализирует исполняемый файл и возвращает CFG в памяти
        :param exe_dist: Путь к исполняемому файлу
        :return: Словарь с CFG {имя_функции: cfg_data}
        """
        if exe_dist in self.cfg_cache:
            return self.cfg_cache[exe_dist]

        try:
            # Открываем бинарник
            r2 = r2pipe.open(exe_dist, flags=["-2"])

            # Выполняем анализ (асинхронно)
            await asyncio.get_event_loop().run_in_executor(None, r2.cmd, "aaa")

            # Получаем список функций
            functions = await asyncio.get_event_loop().run_in_executor(None, r2.cmdj, "aflj")

            if not functions:
                raise ValueError(f"No functions found in {exe_dist}")

            cfg_data = {}

            # Анализируем каждую функцию
            for func in functions:
                func_name = func.get("name", f"unnamed_{func['offset']}")
                func_addr = func["offset"]

                # Получаем CFG для функции
                await asyncio.get_event_loop().run_in_executor(
                    None, r2.cmd, f"agf @ {func_addr}"
                )
                cfg_json = await asyncio.get_event_loop().run_in_executor(
                    None, r2.cmdj, f"agj {func_addr}"
                )

                cfg_data[func_name] = {
                    "offset": func_addr,
                    "cfg": cfg_json,
                    "name": func_name
                }

            # Сохраняем в кэш
            self.cfg_cache[exe_dist] = cfg_data
            return cfg_data

        except Exception as e:
            logging.error(f"Error analyzing {exe_dist}: {e}")
            raise
        finally:
            if 'r2' in locals():
                r2.quit()

    async def get_call_graph(self, exe_dist: str) -> dict:
        """
        Получает граф вызовов и сохраняет в памяти
        :param exe_dist: Путь к исполняемому файлу
        :return: Граф вызовов в виде словаря
        """
        if exe_dist in self.call_graphs:
            return self.call_graphs[exe_dist]

        try:
            r2 = r2pipe.open(exe_dist, flags=["-2"])
            await asyncio.get_event_loop().run_in_executor(None, r2.cmd, "aaa")

            # Получаем граф вызовов
            call_graph = await asyncio.get_event_loop().run_in_executor(
                None, r2.cmdj, "agCj"
            )

            self.call_graphs[exe_dist] = call_graph
            return call_graph

        except Exception as e:
            logging.error(f"Error getting call graph for {exe_dist}: {e}")
            raise
        finally:
            if 'r2' in locals():
                r2.quit()

    async def compare_two_executables(self, exe1: str, exe2: str) -> dict:
        """
        Сравнивает два исполняемых файла, используя данные в памяти
        :return: Результаты сравнения
        """
        # Получаем CFG для обоих файлов
        cfg1, cfg2 = await asyncio.gather(
            self.analyze_executable(exe1),
            self.analyze_executable(exe2)
        )

        # Получаем графы вызовов
        call_graph1, call_graph2 = await asyncio.gather(
            self.get_call_graph(exe1),
            self.get_call_graph(exe2)
        )

        # Здесь можно добавить логику сравнения
        comparison_result = {
            "cfg_comparison": self._compare_cfgs(cfg1, cfg2),
            "call_graph_comparison": self._compare_call_graphs(call_graph1, call_graph2)
        }

        return comparison_result

    def _compare_cfgs(self, cfg1: dict, cfg2: dict) -> dict:
        """Сравнивает CFG двух файлов (заглушка)"""
        # Реализуйте вашу логику сравнения здесь
        return {"similarity": 0.0}  # Заглушка

    def _compare_call_graphs(self, cg1: dict, cg2: dict) -> dict:
        """Сравнивает графы вызовов (заглушка)"""
        # Реализуйте вашу логику сравнения здесь
        return {"similarity": 0.0}  # Заглушка