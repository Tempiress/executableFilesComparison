"""
Function comparison: pairwise function matching between two binaries.

Two strategies:
  - match_functions_custom  — CPU-based similarity (graph + fuzzy hash)
  - match_functions_gpu     — GPU-based embedding similarity (asm2vec)
"""

import concurrent.futures
import copy
import os
import random
import re
import sys
import tempfile
import time
from functools import partial
from pathlib import Path

import numpy as np
import torch
import lancedb
from src.core.similarity_engine import compute_function_similarity


# ---------------------------------------------------------------------------
# Seed
# ---------------------------------------------------------------------------

def set_seed(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


set_seed(42)


# ===================================================================
# Custom (CPU) function matching
# ===================================================================
def chunk_list(lst:list, n:int):
    k, m = divmod(len(lst), n)
    return [lst[i*k + min(i, m): (i + 1) * k + min(i + 1, m)] for i in range(n)]

def _compare_chunk(chunk, functions_a, functions_b, config):
    results = []
    for pair in chunk:
        name_a, name_b = pair
        sim, _ = compute_function_similarity(name_a, name_b, functions_a, functions_b, config)
        results.append({"pair": (name_a, name_b), "sim": sim})
    return results

def _compare_pair(args, functions_a, functions_b, config):
    """Worker: compare a single function pair."""
    name_a, name_b = args
    sim, _ = compute_function_similarity(name_a, name_b, functions_a, functions_b, config)
    return {"pair": (name_a, name_b), "sim": sim}


def match_functions_custom(
    matrix_a, matrix_b, functions_a: dict, functions_b: dict, config
):
    """Match functions between two binaries using graph/hash similarity.

    Enumerates all pairwise combinations, scores them, then greedily
    selects the best non-conflicting matches.

    Returns:
        (matched_a, matched_b)  — list of {new_label, old_label} dicts
    """
    print("Start custom function matching\n")

    # Build all pairs
    pairs = []
    for i in range(1, len(matrix_a)):
        for j in range(1, len(matrix_b)):
            pairs.append((matrix_a[0][i], matrix_b[0][j]))

    print(f"Total comparisons: {len(pairs)}")

    # worker_fn = partial(
    #     _compare_pair,
    #     functions_a=functions_a,
    #     functions_b=functions_b,
    #     config=config,
    # )

    # ThreadPool avoids re-loading torch per worker on Windows
    max_workers = 4 #os.cpu_count() or 4

    chunks = chunk_list(pairs, max_workers)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # future_to_pair = {executor.submit(worker_fn, pair): pair for pair in pairs}
        # scored_pairs = []
        # for future in concurrent.futures.as_completed(future_to_pair):
        #     try:
        #         scored_pairs.append(future.result())
        #     except Exception as exc:
        #         print(f"Error comparing pair: {exc}")

        futures = [executor.submit(_compare_chunk, chunk, functions_a, functions_b, config) for chunk in chunks]
        scored_pairs = []
        for future in concurrent.futures.as_completed(futures):
            scored_pairs.extend(future.result())

    scored_pairs.sort(key=lambda x: x["sim"], reverse=True)

    # Greedy matching
    matched_a, matched_b = [], []
    used_a, used_b = set(), set()
    counter = 0

    for scored in scored_pairs:
        name_a, name_b = scored["pair"]
        if name_a not in used_a and name_b not in used_b:
            matched_a.append({"new_label": counter, "old_label": name_a})
            matched_b.append({"new_label": counter, "old_label": name_b})
            used_a.add(name_a)
            used_b.add(name_b)
            counter += 1

    print("End custom function matching\n")
    return matched_a, matched_b


# ===================================================================
# GPU (asm2vec) function matching
# ===================================================================

# In-process cache keyed by (bin1, bin2, instruction_mode)
_gpu_compare_cache = {}


def _write_functions_to_asm_files(
    functions: dict, output_dir: Path, binary_name: str, config
) -> int:
    """Write per-function .asm files for asm2vec ingestion.

    Returns the number of functions written.
    """
    try:
        from asm2vec_pytorch_master.scripts import bin2asm
    except ImportError:
        from scripts import bin2asm

    use_transformed = config.instructions_mode in ('generalize', 'group', 'both')
    serializer = bin2asm.fn2asm_transformed if use_transformed else bin2asm.fn2asm

    count = 0
    for func_name, func_data in functions.items():
        safe_name = re.sub(r'[<>:\"/\\\\|?*\\x00-\\x1f]', '_', func_name) or f"{func_data['addr']:x}"

        cfg_json = func_data.get('cfg')
        raw_ops = []
        if cfg_json:
            if isinstance(cfg_json, list):
                for item in cfg_json:
                    if isinstance(item, dict):
                        blocks = item.get('blocks', [])
                        if blocks:
                            for block in blocks:
                                raw_ops.extend(block.get('ops', []))
                        else:
                            raw_ops.extend(item.get('ops', []))
            elif isinstance(cfg_json, dict):
                blocks = cfg_json.get('blocks', [])
                if blocks:
                    for block in blocks:
                        raw_ops.extend(block.get('ops', []))
                else:
                    raw_ops.extend(cfg_json.get('ops', []))

        if not raw_ops:
            continue

        asm_text = serializer({'ops': raw_ops, 'name': func_name}, 6)
        if asm_text:
            header = (
                f' .name {func_name}\n'
                f' .offset {func_data["addr"]:016x}\n'
                f' .file {binary_name}\n'
            )
            out_path = output_dir / safe_name
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(header + asm_text)
            count += 1

    return count




def match_functions_gpu(
    matrix_a, matrix_b, functions_a: dict, functions_b: dict, config
):
    """Match functions using asm2vec neural embeddings with LanceDB caching for clear binaries."""
    cache_key = (config.bin1_path, config.bin2_path, config.instructions_mode)
    if cache_key in _gpu_compare_cache:
        print(f"[*] Using cached GPU results for {cache_key}")
        return copy.deepcopy(_gpu_compare_cache[cache_key])

    import asm2vec.utils

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"DEVICE: {device}")

    bin1_name = Path(config.bin1_path).name
    db_path = Path("./.lancedb")
    db = lancedb.connect(str(db_path))
    table_name = "clear_embeddings"

    cached_a = False
    embeddings_a = None
    file_names_a = []

    # Try loading precomputed clear binary embeddings from LanceDB
    if table_name in db.table_names():
        try:
            table = db.open_table(table_name)
            query_str = f"binary_name = '{bin1_name}' AND instruction_mode = '{config.instructions_mode}'"
            arrow_tbl = table.search().where(query_str).limit(10000).to_arrow()
            if len(arrow_tbl) > 0:
                file_names_a = arrow_tbl["function_name"].to_pylist()
                vectors_list = arrow_tbl["vector"].to_pylist()
                embeddings_a = torch.tensor(vectors_list, dtype=torch.float32, device=device)
                embeddings_a = embeddings_a / embeddings_a.norm(dim=1, keepdim=True)
                cached_a = True
                print(f"[*] Loaded {len(file_names_a)} cached embeddings for {bin1_name} ({config.instructions_mode}) from LanceDB")
        except Exception as e:
            print(f"[!] LanceDB cache lookup error: {e}")
            cached_a = False

    with tempfile.TemporaryDirectory(prefix="asm2vec_compare_") as temp_dir:
        temp_path = Path(temp_dir)
        dir_a = temp_path / "bin1"
        dir_b = temp_path / "bin2"
        dir_a.mkdir()
        dir_b.mkdir()

        # Extract & serialize functions to .asm files
        if not cached_a:
            print(f"[*] Extracting functions for {config.bin1_path}...")
            count_a = _write_functions_to_asm_files(functions_a, dir_a, Path(config.bin1_path).name, config)
        else:
            count_a = len(file_names_a)

        print(f"[*] Extracting functions for {config.bin2_path}...")
        count_b = _write_functions_to_asm_files(functions_b, dir_b, Path(config.bin2_path).name, config)

        if count_a == 0 or count_b == 0:
            print("Error: No functions found")
            return [], []

        # Collect file paths for bin2
        file_paths_b, file_names_b = [], []
        for i in range(1, len(matrix_b)):
            fname = matrix_b[0][i]
            fpath = dir_b / fname
            if fpath.exists():
                file_paths_b.append(fpath)
                file_names_b.append(fname)

        if not file_paths_b:
            print("[Error] No valid asm files found for bin2.")
            return [], []

        # Select asm2vec model path
        print("[*] Loading asm2vec model...")
        if config.instructions_mode == 'generalize':
            model_path = "./models/model_generalize.pt"
        elif config.instructions_mode == 'group':
            model_path = "./models/model_group.pt"
        elif config.instructions_mode == 'both':
            model_path = "./models/model_both.pt"
        else:
            model_path = "./asm2vec_pytorch_master/model.pt"

        model, tokens = asm2vec.utils.load_model(model_path, device=device)

        if cached_a:
            # Only run inference/training on bin2 functions
            functions_list_b, tokens_new = asm2vec.utils.load_data(file_paths_b)
            if not functions_list_b:
                print("[Error] bin2 functions did not load.")
                return [], []

            tokens.update(tokens_new)
            model.update(len(functions_list_b), tokens.size())
            model = model.to(device)

            model = asm2vec.utils.train(
                functions_list_b, tokens,
                model=model, epochs=30, device=device,
                mode='test', learning_rate=0.02,
            )

            embeddings_b = model.embeddings_f(torch.arange(len(functions_list_b)).to(device))
            embeddings_b = embeddings_b / embeddings_b.norm(dim=1, keepdim=True)

        else:
            # Collect file paths for bin1
            file_paths_a, file_names_a = [], []
            for i in range(1, len(matrix_a)):
                fname = matrix_a[0][i]
                fpath = dir_a / fname
                if fpath.exists():
                    file_paths_a.append(fpath)
                    file_names_a.append(fname)

            all_files = file_paths_a + file_paths_b
            functions_list, tokens_new = asm2vec.utils.load_data(all_files)

            if not functions_list:
                print("[Error] Functions did not load.")
                return [], []

            tokens.update(tokens_new)
            model.update(len(functions_list), tokens.size())
            model = model.to(device)

            model = asm2vec.utils.train(
                functions_list, tokens,
                model=model, epochs=30, device=device,
                mode='test', learning_rate=0.02,
            )

            # Compute embeddings for both binaries
            all_embeddings = model.embeddings_f(torch.arange(len(functions_list)).to(device))
            n_a = len(file_paths_a)
            embeddings_a = all_embeddings[:n_a]
            embeddings_b = all_embeddings[n_a:]

            embeddings_a = embeddings_a / embeddings_a.norm(dim=1, keepdim=True)
            embeddings_b = embeddings_b / embeddings_b.norm(dim=1, keepdim=True)

            # Save bin1 embeddings to LanceDB
            data_to_save = []
            for fname, vec in zip(file_names_a, embeddings_a.detach().cpu().numpy()):
                data_to_save.append({
                    "binary_name": bin1_name,
                    "instruction_mode": config.instructions_mode,
                    "function_name": fname,
                    "vector": vec.tolist(),
                })

            if data_to_save:
                try:
                    if table_name in db.table_names():
                        table = db.open_table(table_name)
                        try:
                            table.add(data_to_save)
                        except Exception as add_err:
                            print(f"[!] Recreating LanceDB table due to schema change: {add_err}")
                            db.create_table(table_name, data=data_to_save, mode="overwrite")
                    else:
                        db.create_table(table_name, data=data_to_save)
                    print(f"[*] Saved {len(data_to_save)} embeddings for {bin1_name} ({config.instructions_mode}) to LanceDB")
                except Exception as e:
                    print(f"[!] Failed to save embeddings to LanceDB: {e}")

        # Compute cosine similarity matrix
        print("[*] Computing similarity matrix...")
        sim_matrix = torch.mm(embeddings_a, embeddings_b.t())
        sim_matrix_cpu = sim_matrix.detach().cpu().numpy()

        # Greedy pair selection
        print("[*] Finding optimal pairs...")
        pairs = []
        rows, cols = sim_matrix_cpu.shape
        for r in range(rows):
            for c in range(cols):
                pairs.append((float(sim_matrix_cpu[r, c]), file_names_a[r], file_names_b[c]))

        pairs.sort(key=lambda x: x[0], reverse=True)

        matched_a, matched_b = [], []
        used_a, used_b = set(), set()
        counter = 0

        for score, name_a, name_b in pairs:
            if name_a in used_a or name_b in used_b:
                continue
            matched_a.append({"new_label": counter, "old_label": name_a})
            matched_b.append({"new_label": counter, "old_label": name_b})
            used_a.add(name_a)
            used_b.add(name_b)
            counter += 1

    print("End GPU function matching\n")
    _gpu_compare_cache[cache_key] = (matched_a, matched_b)
    return matched_a, matched_b


