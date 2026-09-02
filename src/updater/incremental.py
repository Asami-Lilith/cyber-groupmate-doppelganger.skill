"""增量检查点 - 纯文件头扫描，零解析开销"""
import json, pathlib, time
from pathlib import Path
STATE_PATH = Path(__file__).parent.parent.parent / "data" / "state.json"

def needs_update(history_path, target_uid, state_path=STATE_PATH):
    # 扫描 history 最新 t，不解析全部
    last_t = 0
    try:
        for line in open(history_path, encoding="utf-8"):
            obj = json.loads(line)
            if obj.get("user") == target_uid:
                t = obj.get("t", 0)
                if t > last_t: last_t = t
    except: pass
    state = {}
    if Path(state_path).exists():
        try: state = json.loads(Path(state_path).read_text(encoding="utf-8"))
        except: state = {}
    saved = state.get("groups", {}).get("history", {}).get(target_uid, {}).get("last_t", 0)
    return last_t > saved, last_t

def save_state(history_path, target_uid, last_t, state_path=STATE_PATH):
    p = Path(state_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    state = {}
    if p.exists():
        try: state = json.loads(p.read_text(encoding="utf-8"))
        except: state={}
    state.setdefault("groups", {}).setdefault("history", {})[target_uid] = {"last_t": last_t, "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    # 原子写入
    import tempfile, os
    fd, tmp = tempfile.mkstemp(dir=str(p.parent))
    os.write(fd, json.dumps(state, ensure_ascii=False, indent=2).encode())
    os.fsync(fd); os.close(fd); os.replace(tmp, str(p))
