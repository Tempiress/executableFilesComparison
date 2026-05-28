import logging
import time
from typing import Dict

import r2pipe

import os
import pickle
import hashlib
from pathlib import Path

class CFGAnalyzer:
    def __init__(self):
        self.cfg_cache = {}  # Кэш для хранения CFG в памяти
        self.call_graphs = {}  # Кэш для графов вызовов

    def analyze_executable(self, exe_dist: str, r2:r2pipe = None) -> Dict[str, dict]:
        """
        Анализирует исполняемый файл и возвращает CFG в памяти
        :param exe_dist: Путь к исполняемому файлу
        :return: Словарь с CFG {имя_функции: cfg_data}
        """

        if exe_dist in self.cfg_cache:
            return self.cfg_cache[exe_dist]
        
        r2_provided = r2 is not None 
        try:
            
            if not r2_provided:
                r2 = r2pipe.open(exe_dist, flags=["-2", "-e io.cache=true"])                
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
                f.write(f"Error analyzing {exe_dist} for cfg_cache: {e}\n")
            raise Exception(f"Error analyzing {exe_dist}: {e}")
        
        finally:
            if not r2_provided and r2 is not None:
                r2.quit()

    def get_call_graph(self, exe_dist: str, r2:r2pipe = None) -> dict:
        
        """
        Получает граф вызовов и сохраняет в памяти
        :param exe_dist: Путь к исполняемому файлу
        :return: Граф вызовов в виде словаря
        """

        if exe_dist in self.call_graphs:
            return self.call_graphs[exe_dist]

        r2_provided = r2 is not None
         
        try:

            if not r2_provided:
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
                f.write(f"Error analyzing {exe_dist} for call_graphs: {e}\n")
            raise Exception(f"Error getting call graph for {exe_dist}: {e}")
        finally:
            if not r2_provided and r2 is not None:
                r2.quit()


    def get_analyzers(self, exe_dist: str) -> dict:
        cache_dir = Path(__file__).parent / ".r2_cache"
        cache_dir.mkdir(exist_ok=True)

        abs_path = os.path.abspath(exe_dist)
        path_hash = hashlib.md5(abs_path.encode("utf-8")).hexdigest()

        mtime = int(os.path.getmtime(abs_path))
        size = os.path.getsize(abs_path)

        cache_file = cache_dir / f"cache_{path_hash}_{mtime}_{size}.pkl"
        
        if cache_file.exists():
            try:
                with open(cache_file, "rb") as f:
                    data = pickle.load(f)
                    self.cfg_cache[exe_dist] = data["cfg_data"]
                    self.call_graphs[exe_dist] = data["call_graph"]
                    return self.cfg_cache[exe_dist], self.call_graphs[exe_dist]

            except Exception as e:
                logging.warning(f"Cache file {cache_file} is corrupted: {e}")
                cache_file.unlink()

        
        
        if exe_dist not in self.cfg_cache or exe_dist not in self.call_graphs:
            try: 
                r2 = r2pipe.open(exe_dist, flags=["-2", "-e io.cache=true"])
                r2.cmd("aaa")
                
                if exe_dist not in self.cfg_cache:
                    self.analyze_executable(exe_dist, r2)

                if exe_dist not in self.call_graphs:
                    self.get_call_graph(exe_dist, r2)

                data_to_cache = {
                    "cfg_data": self.cfg_cache[exe_dist],
                    "call_graph": self.call_graphs[exe_dist]
                }
                temp_file = cache_file.with_suffix('.tmp')
                with open(temp_file, "wb") as f:
                    pickle.dump(data_to_cache, f, protocol= pickle.HIGHEST_PROTOCOL)
                os.replace(temp_file, cache_file)

            except Exception as e:
                logging.error(f"Error getting analyzers for {exe_dist}: {e}")
                with open(f"error_log{time.time()}.txt", "a") as f:
                    f.write(f"Error getting analyzers for {exe_dist}: {e}\n")
                raise
            finally:
                if 'r2' in locals():
                    r2.quit()
        return self.cfg_cache[exe_dist], self.call_graphs[exe_dist]