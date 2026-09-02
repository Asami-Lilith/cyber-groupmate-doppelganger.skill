"""持久化幂等 - mid 去重"""
import json
from pathlib import Path
def append_idempotent(history_path, obj):
    mid = obj.get("mid")
    if not mid: 
        open(history_path, "a", encoding="utf-8").write(json.dumps(obj, ensure_ascii=False)+"\n")
        return True
    # 尾部扫描
    try:
        for line in open(history_path, encoding="utf-8"):
            if f'"mid": "{mid}"' in line or f'"mid":"{mid}"' in line:
                return False
    except: pass
    open(history_path, "a", encoding="utf-8").write(json.dumps(obj, ensure_ascii=False)+"\n")
    return True
