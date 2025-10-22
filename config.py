from dataclasses import dataclass
import orjson

@dataclass
class AnalysisConfig:
    hash_type: str = 'ssdeep'
    instructions_mode: str = 'none'  # 'none'|'generalize'|'group'|'both'


def safe_load_json(data):
    if isinstance(data, memoryview):
        data = data.tobytes().decode('utf-8')
    elif isinstance(data, bytes):
        data = data.decode('utf-8')
    elif not isinstance(data, str):
        data = str(data)
    return orjson.loads(data)