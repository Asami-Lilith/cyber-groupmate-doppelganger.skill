#!/usr/bin/env python3
"""独立生成 sticker_rules.json (window=3, 共现统计)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / ".pylib"))
import json
import argparse
from src.processors.sticker_rules import generate as generate_sticker_rules, DEFAULT_TAGS
from src.processors.schemas import atomic_write_json

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

def load_messages():
    msgs=[]
    chunk_dir = DATA_DIR / "recent_messages" / "chunks"
    if chunk_dir.exists():
        for p in sorted(chunk_dir.glob("*.jsonl")):
            for line in open(p, encoding="utf-8"):
                if line.strip(): msgs.append(json.loads(line))
        if msgs: return msgs
    single = DATA_DIR / "recent_messages" / "messages.json"
    if single.exists():
        data=json.loads(single.read_text(encoding="utf-8"))
        if "messages" in data: return data["messages"]
        if isinstance(data, list): return data
    return []

def main():
    ap=argparse.ArgumentParser(description="生成 sticker_rules.json (window=3)")
    ap.add_argument("--window", type=int, default=3)
    ap.add_argument("--tags", default="data/emojis/tags.json")
    ap.add_argument("--out", default="data/emojis/sticker_rules.json")
    args=ap.parse_args()
    msgs=load_messages()
    print(f"loaded {len(msgs)} messages, window={args.window}")
    tags_path = BASE_DIR / args.tags
    tags=None
    if tags_path.exists():
        try:
            tags=json.loads(tags_path.read_text(encoding="utf-8"))
        except: tags=None
    if not tags: tags=DEFAULT_TAGS
    rules=generate_sticker_rules(msgs, tags=tags, window=args.window)
    out = BASE_DIR / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    import time
    meta={"generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "window": args.window, "count_messages": len(msgs), "count_stickers": len(rules), "method": "co-occurrence window=3"}
    # 兼容扁平与结构化：同时提供 rules 字段和顶层扁平
    output={"meta": meta, "rules": rules, **rules, "_meta": meta}
    atomic_write_json(out, output)
    # 同时写结构化备份
    print(f"[sticker_rules] window={args.window} stickers={len(rules)} -> {out}")
    for sid, r in rules.items():
        print(f"  {sid}: freq={r['freq']} when={r['when']}")

if __name__=="__main__":
    main()
