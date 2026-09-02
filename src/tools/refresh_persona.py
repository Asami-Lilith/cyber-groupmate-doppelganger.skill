"""低权限工具 - 宿主调用，无 shell"""
import json
from pathlib import Path
from src.updater.incremental import needs_update, save_state
def refresh_persona(group, uid, history_path, force=False):
    need, last_t = needs_update(history_path, uid)
    if not need and not force:
        return {"updated": False, "reason": "no new messages"}
    # 触发全量：调用现有 pipeline
    import subprocess, sys
    subprocess.run([sys.executable, "scripts/update_recent.py"], check=False)
    subprocess.run([sys.executable, "src/persona/merge.py"], check=False)
    save_state(history_path, uid, last_t)
    return {"updated": True, "last_t": last_t}
