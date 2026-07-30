"""
CFG analysis: extracts control-flow and call graphs from binaries via Radare2.
"""

import hashlib
import logging
import os
import pickle
import time
from pathlib import Path
from typing import Dict, Optional

import r2pipe


class CfgAnalyzer:
    """Extracts CFGs and call graphs from binaries using Radare2."""

    def __init__(self):
        self._cfg_cache: Dict[str, dict] = {}
        self._call_graph_cache: Dict[str, list] = {}

    def analyze_executable(
        self, binary_path: str, r2_pipe: r2pipe = None
    ) -> Dict[str, dict]:
        if binary_path in self._cfg_cache:
            return self._cfg_cache[binary_path]

        pipe_provided = r2_pipe is not None
        try:
            if not pipe_provided:
                r2_pipe = r2pipe.open(binary_path, flags=["-2", "-e io.cache=true"])
                try:
                    r2_pipe.cmd("aaa")
                except Exception as r2_err:
                    logging.warning(f"Full 'aaa' crashed for {binary_path}. Retrying with fallback ('aa')...")
                    r2_pipe = r2pipe.open(binary_path, flags=["-2", "-e io.cache=true"])
                    r2_pipe.cmd("aa")
                    r2_pipe.cmd("aac")
                    r2_pipe.cmd("aar")

            functions = r2_pipe.cmdj("aflj")
            if not functions:
                raise ValueError(f"No functions found in {binary_path}")

            cfg_data = {}
            for func in functions:
                if func.get("nbbs", 0) < 2:
                    continue
                func_name = func.get("name", f"unnamed_{func['addr']}")
                cfg_json = r2_pipe.cmdj(f"agj {func['addr']}")
                cfg_data[func_name] = {
                    "addr": func["addr"], "cfg": cfg_json, "name": func_name,
                }

            self._cfg_cache[binary_path] = cfg_data
            return cfg_data

        except Exception as exc:
            logging.error(f"Error analyzing {binary_path}: {exc}")
            raise

        finally:
            if not pipe_provided and r2_pipe is not None:
                r2_pipe.quit()

    def extract_call_graph(
        self, binary_path: str, r2_pipe: r2pipe = None
    ) -> list:
        if binary_path in self._call_graph_cache:
            return self._call_graph_cache[binary_path]

        pipe_provided = r2_pipe is not None
        try:
            if not pipe_provided:
                r2_pipe = r2pipe.open(binary_path, flags=["-2", "-e io.cache=true"])
                try:
                    r2_pipe.cmd("aaa")
                except Exception as r2_err:
                    logging.warning(f"Full 'aaa' crashed for {binary_path}. Retrying with fallback ('aa')...")
                    r2_pipe = r2pipe.open(binary_path, flags=["-2", "-e io.cache=true"])
                    r2_pipe.cmd("aa")
                    r2_pipe.cmd("aac")
                    r2_pipe.cmd("aar")

            call_graph = r2_pipe.cmdj("agCj")
            self._call_graph_cache[binary_path] = call_graph
            return call_graph

        except Exception as exc:
            logging.error(f"Error extracting call graph for {binary_path}: {exc}")
            raise

        finally:
            if not pipe_provided and r2_pipe is not None:
                r2_pipe.quit()

    def load_analyzers(self, binary_path: str) -> tuple:
        cache_dir = Path(__file__).parent.parent.parent / ".r2_cache"
        cache_dir.mkdir(exist_ok=True)

        abs_path = os.path.abspath(binary_path)
        path_hash = hashlib.md5(abs_path.encode("utf-8")).hexdigest()
        mtime = int(os.path.getmtime(abs_path))
        size = os.path.getsize(abs_path)
        cache_file = cache_dir / f"cache_{path_hash}_{mtime}_{size}.pkl"

        if cache_file.exists():
            try:
                with open(cache_file, "rb") as f:
                    data = pickle.load(f)
                self._cfg_cache[binary_path] = data["cfg_data"]
                self._call_graph_cache[binary_path] = data["call_graph"]
                return data["cfg_data"], data["call_graph"]
            except Exception as exc:
                logging.warning(f"Corrupted cache {cache_file}: {exc}")
                cache_file.unlink()

        if binary_path not in self._cfg_cache or binary_path not in self._call_graph_cache:
            try:
                r2_pipe = r2pipe.open(binary_path, flags=["-2", "-e io.cache=true"])
                try:
                    r2_pipe.cmd("aaa")
                except Exception as r2_err:
                    logging.warning(f"Full 'aaa' crashed for {binary_path}. Retrying with fallback ('aa')...")
                    r2_pipe = r2pipe.open(binary_path, flags=["-2", "-e io.cache=true"])
                    r2_pipe.cmd("aa")
                    r2_pipe.cmd("aac")
                    r2_pipe.cmd("aar")

                if binary_path not in self._cfg_cache:
                    self.analyze_executable(binary_path, r2_pipe)
                if binary_path not in self._call_graph_cache:
                    self.extract_call_graph(binary_path, r2_pipe)

                data_to_cache = {
                    "cfg_data": self._cfg_cache[binary_path],
                    "call_graph": self._call_graph_cache[binary_path],
                }
                temp_file = cache_file.with_suffix('.tmp')
                with open(temp_file, "wb") as f:
                    pickle.dump(data_to_cache, f, protocol=pickle.HIGHEST_PROTOCOL)
                os.replace(temp_file, cache_file)

            except Exception as exc:
                logging.error(f"Error loading analyzers for {binary_path}: {exc}")
                raise
            finally:
                if 'r2_pipe' in locals():
                    r2_pipe.quit()

        return self._cfg_cache[binary_path], self._call_graph_cache[binary_path]
