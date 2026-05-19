from __future__ import annotations

import os
from pathlib import Path


def _find_project_root(start: Path | None = None) -> Path:
    cur = (start or Path(__file__).resolve()).resolve()
    for p in [cur] + list(cur.parents):
        if (p / "config" / "api_keys").exists():
            return p
    return Path(__file__).resolve().parents[1]


def _read_settings_env(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        data[k.strip()] = v.strip().strip('"').strip("'")
    return data


def _split_keys(raw: str) -> list[str]:
    if not raw:
        return []
    parts = []
    for chunk in raw.replace("\n", ",").split(","):
        key = chunk.strip()
        if key:
            parts.append(key)
    return parts


def load_api_keys(start: Path | None = None) -> list[str]:
    root = _find_project_root(start)
    cfg_dir = root / "config"
    key_dir = cfg_dir / "api_keys"
    settings = _read_settings_env(cfg_dir / "settings.env")

    env_multi = os.environ.get("GEMMA_API_KEYS", "")
    env_single = os.environ.get("GEMMA_API_KEY", "")
    if env_multi:
        keys = _split_keys(env_multi)
        if keys:
            return keys
    if env_single.strip():
        return [env_single.strip()]

    set_multi = settings.get("GEMMA_API_KEYS", "")
    set_single = settings.get("GEMMA_API_KEY", "")
    if set_multi:
        keys = _split_keys(set_multi)
        if keys:
            return keys
    if set_single.strip():
        return [set_single.strip()]

    file_multi = (key_dir / "gemma_api_keys.txt")
    file_single = (key_dir / "gemma_api_key.txt")
    if file_multi.exists():
        keys = _split_keys(file_multi.read_text(encoding="utf-8"))
        if keys:
            return keys
    if file_single.exists():
        single = file_single.read_text(encoding="utf-8").strip()
        if single:
            return [single]
    return []


def get_primary_api_key(start: Path | None = None) -> str:
    keys = load_api_keys(start)
    if not keys:
        raise RuntimeError(
            "No API key found. Set GEMMA_API_KEY/GEMMA_API_KEYS or fill config/settings.env "
            "or config/api_keys/gemma_api_key.txt"
        )
    return keys[0]
