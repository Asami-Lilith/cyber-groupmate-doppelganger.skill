"""表情独立通道 - 不进文本词频"""
import json
from collections import Counter
from pathlib import Path

def build_face_freq(messages, out_path):
    cnt = Counter()
    for m in messages:
        for fid in m.get("faces",[]):
            cnt[fid]+=1
    data = {"faces": [{"faceId": fid, "count": c} for fid, c in cnt.most_common(20)]}
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data
