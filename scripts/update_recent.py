#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / ".pylib"))
import json
DATA_DIR = Path(__file__).parent.parent / "data"
from src.processors.extractors import counter_keywords, tfidf_keywords, yake_keywords, textrank_keywords

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
    old = DATA_DIR / "recent_messages" / "messages.jsonl"
    if old.exists():
        return [json.loads(l) for l in open(old, encoding="utf-8") if l.strip()]
    return []

if __name__ == "__main__":
    import argparse, json
    ap=argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--method", choices=["counter","tfidf","yake","textrank"], default="yake")
    args=ap.parse_args()
    if args.demo:
        demo=[
            {"id":"1","sender":{"name":"目标人物"},"content":{"text":"今天好累啊哈哈，破防了呢","elements":[]}},
            {"id":"2","sender":{"name":"目标人物"},"content":{"text":"确实 yyds，明天再摸鱼吧","elements":[]}},
            {"id":"3","sender":{"name":"目标人物"},"content":{"text":"哈哈确实，太难了啊","elements":[]}},
        ]
        (DATA_DIR/"recent_messages").mkdir(parents=True, exist_ok=True)
        (DATA_DIR/"recent_messages"/"messages.json").write_text(json.dumps({"messages": demo}, ensure_ascii=False, indent=2), encoding="utf-8")
        print("demo written (含 啊/呢/吧/哈/yyds)")
    msgs=load_messages()
    if not msgs:
        print("no messages")
    else:
        fn={"counter":counter_keywords,"tfidf":tfidf_keywords,"yake":yake_keywords,"textrank":textrank_keywords}[args.method]
        kws=fn(msgs, top_k=20)
        out=DATA_DIR/"keywords"/"high_freq.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        import hashlib, time
        meta={"generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "source_messages_hash": hashlib.sha256(json.dumps(msgs, ensure_ascii=False).encode()).hexdigest()[:8], "method": args.method, "top_k": len(kws)}
        json.dump({"meta": meta, "keywords": dict(kws)}, open(out,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"[{args.method}] {len(kws)} keywords -> {out}")
        print(kws[:8])
