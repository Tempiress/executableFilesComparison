"""
Fuzzy-hash factory and cached comparison helpers.
All hash-specific libraries are imported lazily.
"""

from functools import lru_cache


def _get_pyssdeep():
    import pyssdeep
    return pyssdeep


def _get_levenshtein():
    import Levenshtein
    return Levenshtein


def _get_tlsh():
    import tlsh
    return tlsh


def _get_nilsimsa():
    from nilsimsa import Nilsimsa, compare_digests
    return Nilsimsa, compare_digests


@lru_cache(maxsize=100_000)
def cached_ppdeep_compare(hash1: str, hash2: str) -> int:
    return _get_pyssdeep().compare(hash1, hash2)


@lru_cache(maxsize=100_000)
def cached_levenshtein(str1: str, str2: str) -> int:
    return _get_levenshtein().distance(str1, str2)


def create_hasher(hash_type: str):
    if hash_type == "ssdeep":
        return _get_pyssdeep().get_hash_buffer

    if hash_type == "tlsh":
        tlsh_mod = _get_tlsh()
        def tlsh_hasher(data):
            if len(data) < 50:
                data += b' ' * (50 - len(data))
            return tlsh_mod.hash(data)
        return tlsh_hasher

    if hash_type == "nilsimsa":
        Nilsimsa, _ = _get_nilsimsa()
        def nilsimsa_hasher(data):
            return Nilsimsa(data).hexdigest()
        return nilsimsa_hasher

    raise ValueError(f"Unsupported hash type: {hash_type}")


# Lazy comparison helpers (for instruction_parser)
def lazy_tlsh_diff(hash_a, hash_b):
    return _get_tlsh().diff(hash_a, hash_b)

def lazy_nilsimsa_compare(hash_a, hash_b) -> int:
    _, cmp = _get_nilsimsa()
    return min(100, int(cmp(hash_a, hash_b) * 100 / 128))

def lazy_fuzz_ratio(hash_a, hash_b):
    from thefuzz import fuzz
    return fuzz.ratio(hash_a, hash_b)
