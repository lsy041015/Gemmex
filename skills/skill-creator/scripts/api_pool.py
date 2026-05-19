"""멀티 API 키 풀 — 라운드로빈 분배 + 429 시 자동 전환."""
import os
import threading
import time
import sys
from pathlib import Path


def _import_shared_loader():
    for p in Path(__file__).resolve().parents:
        if (p / "config" / "key_loader.py").exists():
            sys.path.insert(0, str(p))
            from config.key_loader import load_api_keys as _loader  # type: ignore
            return _loader
    return None


def load_api_keys() -> list[str]:
    """GEMMA_API_KEYS(쉼표 구분) 또는 GEMMA_API_KEY에서 키 목록을 로드."""
    loader = _import_shared_loader()
    if loader:
        keys = loader(Path(__file__).resolve())
        if keys:
            return keys
    multi = os.environ.get("GEMMA_API_KEYS", "")
    if multi:
        keys = [k.strip() for k in multi.split(",") if k.strip()]
        if keys:
            return keys
    single = os.environ.get("GEMMA_API_KEY", "").strip()
    return [single] if single else []


class KeyPool:
    """Thread-safe 라운드로빈 API 키 풀."""

    def __init__(self, keys: list[str]):
        self._keys = keys
        self._rr = 0
        self._until = [0.0] * len(keys)
        self._lock = threading.Lock()

    def get(self) -> tuple[str, int]:
        with self._lock:
            n, now = len(self._keys), time.time()
            for _ in range(n):
                i = self._rr % n
                self._rr += 1
                if now >= self._until[i]:
                    return self._keys[i], i
            i = min(range(n), key=lambda x: self._until[x])
            return self._keys[i], i

    def block(self, idx: int, secs: float = 62.0) -> None:
        with self._lock:
            self._until[idx] = time.time() + secs

    def available(self) -> int:
        now = time.time()
        return sum(1 for t in self._until if now >= t)

    def status(self) -> str:
        return f"{self.available()}/{len(self._keys)} keys available"

    def __len__(self) -> int:
        return len(self._keys)
