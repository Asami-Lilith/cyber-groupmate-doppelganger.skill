#!/usr/bin/env python3
"""
Skill 被调用时执行：增量更新近期数据，反哺给 AI
解决 LLM 记忆/注意力有限问题
"""
import jieba
from collections import Counter
from pathlib import Path
import json

DATA_DIR = Path(__file__).parent.parent / "data"

def extract_keywords(messages, top_k=20):
    words = []
    for m in messages:
        words.extend(jieba.lcut(m))
    # 过滤停用词/单字
    words = [w for w in words if len(w) > 1]
    return Counter(words).most_common(top_k)

if __name__ == "__main__":
    # 示例：从 recent_messages 读取，产出 keywords
    recent_file = DATA_DIR / "recent_messages" / "messages.jsonl"
    if recent_file.exists():
        msgs = [json.loads(l)["text"] for l in open(recent_file)]
        kws = extract_keywords(msgs)
        out = DATA_DIR / "keywords" / "high_freq.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        json.dump(dict(kws), open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"updated {len(kws)} keywords -> {out}")
    else:
        print("no recent messages yet, skip")
