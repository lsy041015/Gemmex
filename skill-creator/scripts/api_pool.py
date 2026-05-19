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
    """GEMMA_API_KEYS (쉼표 구분) 또는 GEMMA_API_KEY에서 키 목록을 로드합니다."""
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
        self._keys  = keys
        self._rr    = 0
        self._until = [0.0] * len(keys)  # 각 키의 블록 해제 타임스탬프
        self._lock  = threading.Lock()

    def get(self) -> tuple[str, int]:
        """(key, index) — 사용 가능한 키를 라운드로빈으로 반환합니다."""
        with self._lock:
            n, now = len(self._keys), time.time()
            for _ in range(n):
                i = self._rr % n
                self._rr += 1
                if now >= self._until[i]:
                    return self._keys[i], i
            # 모든 키 블록됨 → 가장 빨리 풀리는 키 반환
            i = min(range(n), key=lambda x: self._until[x])
            return self._keys[i], i

    def block(self, idx: int, secs: float = 62.0) -> None:
        """키를 일시적으로 사용 불가 처리합니다 (기본 62초)."""
        with self._lock:
            self._until[idx] = time.time() + secs

    def available(self) -> int:
        """현재 사용 가능한 키 수를 반환합니다."""
        now = time.time()
        return sum(1 for t in self._until if now >= t)

    def status(self) -> str:
        return f"{self.available()}/{len(self._keys)}개 키 사용 가능"

    def __len__(self) -> int:
        return len(self._keys)
