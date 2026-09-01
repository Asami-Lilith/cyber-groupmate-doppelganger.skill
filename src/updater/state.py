"""Incremental checkpoint .state.json for data pipeline (atomic write).

Re-exports core helpers from src/processors/schemas.py for ergonomic import
as `from src.updater.state import load_state, save_state`.

The checkpoint records the last processed message id/timestamp and source hash
so the pipeline can skip already-processed chunks on re-run (idempotent replay).
"""

from pathlib import Path
from typing import Any, Dict, List, Union

from src.processors.schemas import (
    STATE_FILENAME,
    STATE_SCHEMA,
    STATE_VERSION,
    atomic_write_json,
    default_state,
    get_state_path,
    load_state,
    save_state,
    update_state,
    should_process,
    is_incremental_update_needed,
    validate_state,
)

# Also expose a simple Checkpoint class for OOP-style usage in tests/pipeline
class Checkpoint:
    """Tiny wrapper around .state.json file with atomic persistence."""

    def __init__(self, path: Union[str, Path, None] = None, *, data_dir: Union[str, Path, None] = None):
        self.path = Path(get_state_path(data_dir=data_dir) if path is None else path)
        self._state: Dict[str, Any] = load_state(self.path)

    @property
    def state(self) -> Dict[str, Any]:
        return self._state

    def load(self) -> Dict[str, Any]:
        self._state = load_state(self.path)
        return self._state

    def save(self, state: Dict[str, Any] | None = None) -> Path:
        if state is not None:
            self._state = state
        return save_state(self._state, self.path)

    def update(self, messages: List[Dict[str, Any]], *, processed_chunks: List[str] | None = None, source_hash: str | None = None, method: str | None = None) -> Dict[str, Any]:
        self._state = update_state(messages, processed_chunks=processed_chunks, source_hash=source_hash, method=method, path=self.path)
        return self._state

    def should_process(self, new_hash: str) -> bool:
        return should_process(new_hash, self._state)

__all__ = [
    "Checkpoint",
    "STATE_FILENAME",
    "STATE_SCHEMA",
    "STATE_VERSION",
    "load_state",
    "save_state",
    "update_state",
    "should_process",
    "is_incremental_update_needed",
    "get_state_path",
    "default_state",
    "validate_state",
    "atomic_write_json",
]
