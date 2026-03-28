import hashlib
import json
import pickle
from pathlib import Path


class LocalDiskCache:
    def __init__(self, cache_dir):
        self.cache_dir = Path(cache_dir)
        if not self.cache_dir.exists():
            self.cache_dir.mkdir(parents=True)

    def get_cached(self, key):
        key_hash = self.md5_of_nested_dict(key)
        if (self.cache_dir/key_hash).exists():
            with open (self.cache_dir/key_hash, "rb") as f:
                return pickle.load(f), key_hash
        return None, key_hash

    def md5_of_nested_dict(self, data: dict) -> str:
        canonical = json.dumps(
            data,
            sort_keys=True,  # ensures dict key order is stable
            separators=(",", ":"),  # removes whitespace differences
            ensure_ascii=False  # optional, but consistent for unicode
        )
        return hashlib.md5(canonical.encode("utf-8")).hexdigest()

    def cache(self, key, text_stream, final_messages):
        with open(self.cache_dir/key, "wb") as f:
            pickle.dump(dict(text_stream= text_stream, final_messages= final_messages), f)
