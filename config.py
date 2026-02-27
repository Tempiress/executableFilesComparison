from dataclasses import dataclass
import orjson

@dataclass
class AnalysisConfig:
    hash_type: str = 'ssdeep'   # 'ssdeep' | 'nilsimsa'
    instructions_mode: str = 'none'  # 'none'|'generalize'|'group'|'both'
    asm2vec_mode: bool = False
    compare_mode: str = 'GPU'   # 'GPU' | 'custom'
    bin1_path: str = 'none'
    bin2_path: str = 'none'


def safe_load_json(data):
    # Если это уже распаршенный словарь — просто возвращаем его
    if isinstance(data, dict):
        return data

    if isinstance(data, memoryview):
        data = data.tobytes().decode('utf-8')
    elif isinstance(data, bytes):
        data = data.decode('utf-8')
    elif not isinstance(data, str):
        data = str(data)
    return orjson.loads(data)