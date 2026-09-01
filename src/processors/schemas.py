"""Schemas for data pipeline: high_freq.json, manifest.json and incremental checkpoint .state.json.

Provides:
- JSON Schema dicts (draft-07 compatible) for high_freq.json and manifest.json
- Validation helpers (pure stdlib, no external deps; optionally uses jsonschema if installed)
- Atomic write helpers for crash-safe pipeline writes
- Incremental checkpoint state helpers for .state.json

All writes in the data pipeline should go through atomic_write_json / atomic_write_text
to avoid partial/corrupt files on crash or power loss.

Typical pipeline usage:
    from src.processors.schemas import (
        HIGH_FREQ_SCHEMA, MANIFEST_SCHEMA, STATE_SCHEMA,
        validate_high_freq, validate_manifest, validate_state,
        atomic_write_json, load_state, save_state,
    )
"""

from __future__ import annotations

import json
import os
import re
import hashlib
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple, Union

# ---------------------------------------------------------------------------
# ISO 8601 helper
# ---------------------------------------------------------------------------

_ISO8601_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
)

def _is_iso8601(s: str) -> bool:
    if not isinstance(s, str):
        return False
    if _ISO8601_RE.match(s):
        return True
    # also accept with timezone offset
    try:
        # Python's fromisoformat doesn't handle Z, so replace
        iso = s.replace("Z", "+00:00")
        datetime.fromisoformat(iso)
        return True
    except Exception:
        return False

def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# ---------------------------------------------------------------------------
# JSON Schemas (draft-07)
# ---------------------------------------------------------------------------

HIGH_FREQ_SCHEMA: Dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "high_freq.json",
    "description": "Top-K keywords extracted from recent messages (jieba + scorers)",
    "type": "object",
    "required": ["meta", "keywords"],
    "additionalProperties": False,
    "properties": {
        "meta": {
            "type": "object",
            "required": ["generated_at", "source_messages_hash", "method", "top_k"],
            "additionalProperties": False,
            "properties": {
                "generated_at": {"type": "string", "format": "date-time", "description": "UTC ISO8601"},
                "source_messages_hash": {
                    "type": "string",
                    "pattern": "^[a-f0-9]{4,64}$",
                    "description": "hex hash of source messages (8 chars truncated sha256)"
                },
                "method": {
                    "type": "string",
                    "enum": ["counter", "tfidf", "yake", "textrank"],
                    "description": "keyword extraction method"
                },
                "top_k": {"type": "integer", "minimum": 0, "maximum": 1000},
            },
        },
        "keywords": {
            "type": "object",
            "description": "word -> score mapping",
            "patternProperties": {
                "^.+$": {"type": "number", "minimum": 0}
            },
            "additionalProperties": False,
        },
    },
}

MANIFEST_SCHEMA: Dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "manifest.json",
    "description": "Chunk manifest for data/recent_messages/chunks/",
    "type": "object",
    "required": ["chunks", "iteration", "count", "generated_at"],
    "additionalProperties": False,
    "properties": {
        "chunks": {
            "type": "array",
            "description": "ordered list of chunk filenames",
            "items": {"type": "string", "pattern": r"^c\d+\.jsonl$"},
            "minItems": 0,
        },
        "iteration": {"type": "integer", "minimum": 0, "description": "pipeline iteration"},
        "count": {"type": "integer", "minimum": 0, "description": "total message count across chunks"},
        "generated_at": {"type": "string", "format": "date-time"},
    },
}

STATE_SCHEMA: Dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": ".state.json",
    "description": "Incremental checkpoint for data pipeline (crash-safe, idempotent replay)",
    "type": "object",
    "required": ["version", "last_id", "last_timestamp", "processed_count", "processed_chunks", "source_hash", "updated_at"],
    "additionalProperties": False,
    "properties": {
        "version": {"type": "integer", "minimum": 1, "description": "schema version"},
        "last_id": {"type": ["string", "null"], "description": "last processed message id"},
        "last_timestamp": {"type": ["integer", "null"], "minimum": 0, "description": "last processed timestamp ms"},
        "processed_count": {"type": "integer", "minimum": 0},
        "processed_chunks": {
            "type": "array",
            "items": {"type": "string"},
        },
        "source_hash": {"type": "string", "description": "hash of last processed messages payload"},
        "updated_at": {"type": "string", "format": "date-time"},
        "method": {"type": "string", "enum": ["counter", "tfidf", "yake", "textrank"]},
    },
}

# ---------------------------------------------------------------------------
# Pure-python validators (no jsonschema dep required)
# ---------------------------------------------------------------------------

def _validate_iso8601_field(value: Any, field: str):
    if not isinstance(value, str) or not _is_iso8601(value):
        raise ValueError(f"{field} must be ISO8601 UTC string, got {value!r}")

def validate_high_freq(data: Dict[str, Any]) -> bool:
    """Validate high_freq.json structure. Raises ValueError/TypeError on invalid, returns True on valid."""
    if not isinstance(data, dict):
        raise TypeError("high_freq.json must be object")
    if "meta" not in data or "keywords" not in data:
        raise ValueError("high_freq.json missing required keys 'meta'/'keywords'")
    if set(data.keys()) != {"meta", "keywords"}:
        # allow only those two at top-level per schema
        extra = set(data.keys()) - {"meta", "keywords"}
        if extra:
            raise ValueError(f"high_freq.json extra top-level keys: {extra}")

    meta = data["meta"]
    if not isinstance(meta, dict):
        raise TypeError("meta must be object")
    for k in ("generated_at", "source_messages_hash", "method", "top_k"):
        if k not in meta:
            raise ValueError(f"meta missing required field '{k}'")
    _validate_iso8601_field(meta["generated_at"], "meta.generated_at")
    if not isinstance(meta["source_messages_hash"], str) or not re.match(r"^[a-f0-9]{4,64}$", meta["source_messages_hash"]):
        raise ValueError(f"meta.source_messages_hash must be hex hash, got {meta['source_messages_hash']!r}")
    if meta["method"] not in ("counter", "tfidf", "yake", "textrank"):
        raise ValueError(f"meta.method must be one of counter/tfidf/yake/textrank, got {meta['method']!r}")
    if not isinstance(meta["top_k"], int) or not (0 <= meta["top_k"] <= 1000):
        raise ValueError(f"meta.top_k must be int 0..1000, got {meta['top_k']!r}")

    kws = data["keywords"]
    if not isinstance(kws, dict):
        raise TypeError("keywords must be object")
    for word, score in kws.items():
        if not isinstance(word, str) or not word:
            raise ValueError(f"keyword key must be non-empty string, got {word!r}")
        if not isinstance(score, (int, float)):
            raise ValueError(f"keyword score for {word!r} must be number, got {score!r}")
        if score < 0:
            raise ValueError(f"keyword score for {word!r} must be >=0, got {score}")
        # optional: check not NaN/inf
        if isinstance(score, float) and (score != score or score == float('inf') or score == float('-inf')):
            raise ValueError(f"keyword score for {word!r} must be finite, got {score}")
    # cross-check top_k vs actual count (allow <=, but warn if mismatch >0)
    if meta["top_k"] != len(kws):
        # not strict error for flexibility: allow meta.top_k to reflect requested k even if fewer words available
        # but if keywords more than top_k, it's inconsistent
        if len(kws) > meta["top_k"] and meta["top_k"] != 0:
            raise ValueError(f"keywords count {len(kws)} exceeds meta.top_k {meta['top_k']}")
    return True

def validate_manifest(data: Dict[str, Any]) -> bool:
    """Validate manifest.json. Raises on invalid, returns True on valid."""
    if not isinstance(data, dict):
        raise TypeError("manifest.json must be object")
    for k in ("chunks", "iteration", "count", "generated_at"):
        if k not in data:
            raise ValueError(f"manifest.json missing required field '{k}'")
    extra = set(data.keys()) - {"chunks", "iteration", "count", "generated_at"}
    if extra:
        raise ValueError(f"manifest.json extra keys: {extra}")

    chunks = data["chunks"]
    if not isinstance(chunks, list):
        raise TypeError("chunks must be array")
    for c in chunks:
        if not isinstance(c, str) or not re.match(r"^c\d+\.jsonl$", c):
            raise ValueError(f"chunk entry must match c{{number}}.jsonl, got {c!r}")
    if not isinstance(data["iteration"], int) or data["iteration"] < 0:
        raise ValueError(f"iteration must be int >=0, got {data['iteration']!r}")
    if not isinstance(data["count"], int) or data["count"] < 0:
        raise ValueError(f"count must be int >=0, got {data['count']!r}")
    _validate_iso8601_field(data["generated_at"], "generated_at")
    # optional consistency: count should be >= chunks length if chunks non-empty
    return True

def validate_state(data: Dict[str, Any]) -> bool:
    """Validate .state.json checkpoint. Raises on invalid, returns True on valid."""
    if not isinstance(data, dict):
        raise TypeError(".state.json must be object")
    for k in ("version", "last_id", "last_timestamp", "processed_count", "processed_chunks", "source_hash", "updated_at"):
        if k not in data:
            raise ValueError(f".state.json missing required field '{k}'")
    extra = set(data.keys()) - {"version", "last_id", "last_timestamp", "processed_count", "processed_chunks", "source_hash", "updated_at", "method"}
    if extra:
        raise ValueError(f".state.json extra keys: {extra}")
    if not isinstance(data["version"], int) or data["version"] < 1:
        raise ValueError(f"version must be int >=1, got {data['version']!r}")
    if data["last_id"] is not None and not isinstance(data["last_id"], str):
        raise ValueError(f"last_id must be string or null, got {data['last_id']!r}")
    if data["last_timestamp"] is not None and (not isinstance(data["last_timestamp"], int) or data["last_timestamp"] < 0):
        raise ValueError(f"last_timestamp must be int >=0 or null, got {data['last_timestamp']!r}")
    if not isinstance(data["processed_count"], int) or data["processed_count"] < 0:
        raise ValueError(f"processed_count must be int >=0, got {data['processed_count']!r}")
    if not isinstance(data["processed_chunks"], list) or not all(isinstance(x, str) for x in data["processed_chunks"]):
        raise ValueError("processed_chunks must be array of strings")
    if not isinstance(data["source_hash"], str):
        raise ValueError(f"source_hash must be string, got {data['source_hash']!r}")
    _validate_iso8601_field(data["updated_at"], "updated_at")
    if "method" in data and data["method"] not in ("counter", "tfidf", "yake", "textrank"):
        raise ValueError(f"method must be known method, got {data['method']!r}")
    return True

def validate(data: Dict[str, Any], kind: str) -> bool:
    """Generic validate dispatcher: kind in ('high_freq', 'manifest', 'state')."""
    if kind == "high_freq":
        return validate_high_freq(data)
    if kind == "manifest":
        return validate_manifest(data)
    if kind == "state":
        return validate_state(data)
    raise ValueError(f"unknown schema kind {kind!r}")

# ---------------------------------------------------------------------------
# Optional jsonschema integration (if installed)
# ---------------------------------------------------------------------------

def _jsonschema_validate(data: Dict[str, Any], schema: Dict[str, Any]):
    try:
        import jsonschema  # type: ignore
        jsonschema.validate(data, schema)
        return True
    except ImportError:
        return None  # fallback to manual
    except Exception as e:
        raise ValueError(str(e)) from e

def validate_with_jsonschema(data: Dict[str, Any], kind: str) -> bool:
    mapping = {"high_freq": HIGH_FREQ_SCHEMA, "manifest": MANIFEST_SCHEMA, "state": STATE_SCHEMA}
    schema = mapping.get(kind)
    if schema is None:
        raise ValueError(f"unknown kind {kind!r}")
    res = _jsonschema_validate(data, schema)
    if res is None:
        return validate(data, kind)
    return True

# ---------------------------------------------------------------------------
# Atomic write helpers
# ---------------------------------------------------------------------------

def atomic_write(path: Union[str, Path], data: Union[str, bytes], *, mode: str = "w", encoding: str = "utf-8") -> Path:
    """Atomically write text or bytes to path.

    Writes to a temp file in the same directory then os.replace (atomic on POSIX/Windows).
    Ensures parent dirs exist, flushes and fsyncs before rename.

    Returns the final Path.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    # create temp in same dir for atomic rename
    fd, tmp_path = tempfile.mkstemp(dir=str(p.parent), prefix="." + p.name + ".tmp.")
    try:
        if "b" in mode:
            # bytes
            if isinstance(data, str):
                data = data.encode(encoding)
            os.write(fd, data)  # type: ignore
        else:
            # text
            if isinstance(data, bytes):
                data = data.decode(encoding)
            # use os.fdopen to handle encoding correctly
            with os.fdopen(fd, mode, encoding=encoding) as f:
                f.write(data)  # type: ignore
                f.flush()
                os.fsync(f.fileno())
            # fd already closed via fdopen, avoid double close
            fd = -1
            # fsync directory for durability (best effort)
            try:
                dir_fd = os.open(str(p.parent), os.O_DIRECTORY)
                try:
                    os.fsync(dir_fd)
                finally:
                    os.close(dir_fd)
            except Exception:
                pass
            os.replace(tmp_path, str(p))
            # fsync parent again after replace
            try:
                dir_fd = os.open(str(p.parent), os.O_DIRECTORY)
                try:
                    os.fsync(dir_fd)
                finally:
                    os.close(dir_fd)
            except Exception:
                pass
            return p
        # bytes path: flush/fsync manually
        os.fsync(fd)
        os.close(fd)
        fd = -1
        os.replace(tmp_path, str(p))
        return p
    finally:
        if fd != -1:
            try:
                os.close(fd)
            except Exception:
                pass
        # cleanup temp if still exists (on failure)
        try:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except Exception:
            pass

def atomic_write_json(path: Union[str, Path], obj: Any, *, indent: int = 2, ensure_ascii: bool = False, sort_keys: bool = False) -> Path:
    """Atomically write JSON object to path with validation of parent dir.

    Serializes with json.dumps then atomic_write.
    """
    text = json.dumps(obj, ensure_ascii=ensure_ascii, indent=indent, sort_keys=sort_keys)
    # ensure trailing newline for POSIX friendliness
    if not text.endswith("\n"):
        text += "\n"
    return atomic_write(path, text, mode="w", encoding="utf-8")

def atomic_write_text(path: Union[str, Path], text: str, *, encoding: str = "utf-8") -> Path:
    return atomic_write(path, text, mode="w", encoding=encoding)

# Compatibility aliases for pipeline code that may import different names
atomic_write_file = atomic_write
safe_write_json = atomic_write_json

# ---------------------------------------------------------------------------
# Incremental checkpoint .state.json helpers
# ---------------------------------------------------------------------------

STATE_FILENAME = ".state.json"
STATE_VERSION = 1

def default_state() -> Dict[str, Any]:
    return {
        "version": STATE_VERSION,
        "last_id": None,
        "last_timestamp": None,
        "processed_count": 0,
        "processed_chunks": [],
        "source_hash": "",
        "updated_at": _now_iso(),
    }

def get_state_path(data_dir: Union[str, Path, None] = None, *, base: Union[str, Path, None] = None) -> Path:
    """Return canonical .state.json path.

    Priority:
    - if base is given, treat as direct file or dir
    - if data_dir given, returns data_dir/.state.json (or if data_dir points to chunks dir, use that dir)
    - otherwise defaults to data/recent_messages/chunks/.state.json relative to this file
    """
    if base is not None:
        b = Path(base)
        if b.suffix == ".json":
            return b
        return b / STATE_FILENAME
    if data_dir is not None:
        d = Path(data_dir)
        # if it looks like a file, use its parent
        if d.suffix == ".json":
            return d.parent / STATE_FILENAME
        return d / STATE_FILENAME
    # default: project data/recent_messages/chunks/.state.json
    here = Path(__file__).resolve()
    # walk up to find project root containing data/
    for parent in here.parents:
        candidate = parent / "data" / "recent_messages" / "chunks" / STATE_FILENAME
        # we return the chunks variant as primary; pipeline will ensure it exists
        if (parent / "data").exists() or parent.name == "cyber-groupmate-doppelganger.skill":
            return candidate
    # fallback relative to processors dir
    return here.parent.parent.parent / "data" / "recent_messages" / "chunks" / STATE_FILENAME

def load_state(path: Union[str, Path, None] = None, *, data_dir: Union[str, Path, None] = None) -> Dict[str, Any]:
    """Load and validate .state.json, returning default_state() if missing or corrupt."""
    if path is None:
        path = get_state_path(data_dir=data_dir)
    p = Path(path)
    if not p.exists():
        return default_state()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        validate_state(data)
        return data
    except Exception:
        # corrupt -> return default but keep hash for debugging
        return default_state()

def save_state(state: Dict[str, Any], path: Union[str, Path, None] = None, *, data_dir: Union[str, Path, None] = None) -> Path:
    """Validate and atomically write state to .state.json. Returns final path."""
    validate_state(state)
    if path is None:
        path = get_state_path(data_dir=data_dir)
    # ensure updated_at refreshed if not set
    if "updated_at" not in state or not state["updated_at"]:
        state["updated_at"] = _now_iso()
    return atomic_write_json(path, state)

def update_state(
    messages: List[Dict[str, Any]],
    *,
    processed_chunks: List[str] | None = None,
    source_hash: str | None = None,
    method: str | None = None,
    path: Union[str, Path, None] = None,
    data_dir: Union[str, Path, None] = None,
) -> Dict[str, Any]:
    """Build new state dict from current messages batch and atomically persist.

    Computes last_id/last_timestamp from messages sorted by timestamp/id.
    If source_hash not given, computes sha256 of json dump (truncated 8 chars).
    Returns the new state dict.
    """
    if processed_chunks is None:
        processed_chunks = []
    if source_hash is None:
        try:
            source_hash = hashlib.sha256(json.dumps(messages, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:8]
        except Exception:
            source_hash = ""
    last_id = None
    last_ts = None
    if messages:
        # pick max timestamp, fallback to last element's id
        try:
            sorted_msgs = sorted(messages, key=lambda m: (m.get("timestamp", 0) or 0, m.get("id", "")))
            last = sorted_msgs[-1]
            last_id = last.get("id")
            last_ts = last.get("timestamp")
            if last_ts is not None:
                last_ts = int(last_ts)
        except Exception:
            last = messages[-1]
            last_id = last.get("id")
            last_ts = last.get("timestamp")

    state = {
        "version": STATE_VERSION,
        "last_id": last_id,
        "last_timestamp": last_ts,
        "processed_count": len(messages),
        "processed_chunks": sorted(set(processed_chunks)),
        "source_hash": source_hash or "",
        "updated_at": _now_iso(),
    }
    if method:
        state["method"] = method
    # validate before write
    validate_state(state)
    # atomic persist
    save_state(state, path=path, data_dir=data_dir)
    return state

def should_process(new_hash: str, state: Dict[str, Any] | None = None, *, path: Union[str, Path, None] = None, data_dir: Union[str, Path, None] = None) -> bool:
    """Return True if new messages hash differs from checkpoint (incremental check)."""
    if state is None:
        state = load_state(path=path, data_dir=data_dir)
    return state.get("source_hash") != new_hash

def is_incremental_update_needed(messages: List[Dict[str, Any]], *, path: Union[str, Path, None] = None, data_dir: Union[str, Path, None] = None) -> Tuple[bool, Dict[str, Any]]:
    """Check if messages differ from checkpoint. Returns (needed, state)."""
    try:
        h = hashlib.sha256(json.dumps(messages, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:8]
    except Exception:
        h = ""
    st = load_state(path=path, data_dir=data_dir)
    return (st.get("source_hash") != h, st)

# ---------------------------------------------------------------------------
# Convenience loader that auto-chooses pipeline data_dir
# ---------------------------------------------------------------------------

def resolve_data_dir(hint: Union[str, Path, None] = None) -> Path:
    if hint is not None:
        return Path(hint)
    # try to find data dir relative to this file
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "data" / "recent_messages").exists():
            return parent / "data"
        if parent.name == "cyber-groupmate-doppelganger.skill":
            cand = parent / "data"
            if cand.exists():
                return cand
    # fallback: assume cwd-relative
    return Path("data")

__all__ = [
    "HIGH_FREQ_SCHEMA",
    "MANIFEST_SCHEMA",
    "STATE_SCHEMA",
    "validate_high_freq",
    "validate_manifest",
    "validate_state",
    "validate",
    "validate_with_jsonschema",
    "atomic_write",
    "atomic_write_json",
    "atomic_write_text",
    "atomic_write_file",
    "safe_write_json",
    "STATE_FILENAME",
    "STATE_VERSION",
    "default_state",
    "get_state_path",
    "load_state",
    "save_state",
    "update_state",
    "should_process",
    "is_incremental_update_needed",
    "resolve_data_dir",
]
