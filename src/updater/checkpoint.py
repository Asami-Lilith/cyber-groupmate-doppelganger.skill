"""Alias for incremental checkpoint — re-export from state.py"""
from .state import *  # noqa: F401,F403
from .state import Checkpoint, load_state, save_state, update_state, should_process, get_state_path  # noqa: F401
