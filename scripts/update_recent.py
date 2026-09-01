#!/usr/bin/env python3
"""
Skill 被调用时执行：增量更新近期数据，反哺给 AI
兼容 qq-chat-exporter CleanMessage JSON 格式
- 单文件: data/recent_messages/messages.json {messages: [CleanMessage]}
- 流式: data/recent_messages/chunks/*.jsonl 每行一个 CleanMessage
- 兼容旧格式: {"text": "..."}
"""
import json
from pathlib import Path
from collections import Counter
try:
    import jieba
    HAS_JIEBA=True
    
except ImportError:
    HAS_JIEBA=False

DATA_DIR = Path(__file__).parent.parent / "data"

def get_text(msg):
    # 兼容 CleanMessage 和旧格式
    if "content" in msg:
        return msg["content"].get("text", "")
    return msg.get("text", "")

# 映射表: config/uid_mapping.json <群ID, openID> -> 展示名（QQ官方Bot只能拿到openID）
def get_sender_name(msg):
    if "sender" in msg:
        return msg["sender"].get("name", "")
    return msg.get("sender", {}).get("name","") if isinstance(msg.get("sender"), dict) else str(msg.get("sender",""))

def extract_keywords(messages, top_k=20):
    if not HAS_JIEBA:
        # fallback: 字符级
        from collections import Counter
        words = [c for m in messages for c in get_text(m) if len(c)>1]
        return Counter(words).most_common(top_k)
    words=[]
    for m in messages:
        t=get_text(m)
        if t:
            words.extend(jieba.lcut(t))
    words=[w for w in words if len(w)>1]
    return Counter(words).most_common(top_k)

def load_messages():
    msgs=[]
    # 优先 jsonl chunked
    chunk_dir = DATA_DIR / "recent_messages" / "chunks"
    if chunk_dir.exists():
        for p in sorted(chunk_dir.glob("*.jsonl")):
            for line in open(p, encoding="utf-8"):
                line=line.strip()
                if line:
                    msgs.append(json.loads(line))
        if msgs:
            return msgs
    # 单文件 messages.json
    single = DATA_DIR / "recent_messages" / "messages.json"
    if single.exists():
        data=json.loads(single.read_text(encoding="utf-8"))
        if "messages" in data:
            return data["messages"]
        if isinstance(data, list):
            return data
    # 旧格式 messages.jsonl
    old = DATA_DIR / "recent_messages" / "messages.jsonl"
    if old.exists():
        return [json.loads(l) for l in open(old, encoding="utf-8") if l.strip()]
    return []

if __name__=="__main__":
    import sys
    if "--demo" in sys.argv:
        demo=[
            {"id":"1","sender":{"name":"目标人物"},"content":{"text":"今天好累哈哈","elements":[]}},
            {"id":"2","sender":{"name":"目标人物"},"content":{"text":"破防了确实","elements":[]}}
        ]
        (DATA_DIR/"recent_messages").mkdir(parents=True, exist_ok=True)
        (DATA_DIR/"recent_messages"/"messages.json").write_text(json.dumps({"messages": demo}, ensure_ascii=False, indent=2), encoding="utf-8")
        print("demo data written to messages.json (CleanMessage format)")
    msgs=load_messages()
    if not msgs:
        print("no recent messages yet, skip")
    else:
        kws=extract_keywords(msgs)
        out=DATA_DIR/"keywords"/"high_freq.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        json.dump(dict(kws), open(out,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"updated {len(kws)} keywords -> {out}")
