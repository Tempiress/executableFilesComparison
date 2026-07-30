"""
Analysis configuration and JSON helpers.
"""

from dataclasses import dataclass

import orjson


VALID_HASH_TYPES = ('ssdeep', 'nilsimsa', 'tlsh')
VALID_INSTRUCTION_MODES = ('none', 'generalize', 'group', 'both', 'group_only')
VALID_COMPARE_MODES = ('GPU', 'custom')


@dataclass
class AnalysisConfig:
    """Configuration for a binary comparison run."""

    hash_type: str = 'ssdeep'
    instructions_mode: str = 'none'
    asm2vec_mode: bool = False
    compare_mode: str = 'GPU'
    bin1_path: str = 'none'
    bin2_path: str = 'none'

    def __post_init__(self):
        if (
            self.hash_type not in VALID_HASH_TYPES
            or self.instructions_mode not in VALID_INSTRUCTION_MODES
            or self.compare_mode not in VALID_COMPARE_MODES
        ):
            raise AttributeError("Invalid analysis config values")


def safe_load_json(data):
    """Parse JSON from various input types (str, bytes, memoryview, dict)."""
    if isinstance(data, dict):
        return data
    if isinstance(data, memoryview):
        data = data.tobytes().decode('utf-8')
    elif isinstance(data, bytes):
        data = data.decode('utf-8')
    elif not isinstance(data, str):
        data = str(data)
    return orjson.loads(data)
