#!/usr/bin/env python3
"""
Sticker rules generation: context window 3, co-occurrence stats
- 每张表情包前 N=3 条消息作为触发场景
- 统计 sticker_id -> {trigger_keywords: Counter, categories: Counter, freq, examples}
- 产出 data/emojis/sticker_rules.json
"""
import json
from pathlib import Path
from collections import Counter, defaultdict
from .tokenizer import tokenize

DEFAULT_TAGS = {
    "dog_head.png": {"label": "狗头保命", "emotion": "teasing", "keywords": ["破防", "离谱", "玩笑"]},
    "cry_laugh.png": {"label": "笑哭", "emotion": "joy", "keywords": ["哈哈", "笑死", "好笑"]},
    "angry.png": {"label": "生气", "emotion": "anger", "keywords": ["离谱", "破防", "难顶"]},
    "thumb_up.png": {"label": "点赞", "emotion": "positive", "keywords": ["确实", "不错", "yyds", "好用"]},
}

def extract_sticker_id(msg):
    """从 CleanMessage 中提取 sticker 文件名，兼容多种格式"""
    # 1. elements: type == image
    for el in msg.get("content", {}).get("elements", []):
        if el.get("type") == "image":
            data = el.get("data", {})
            fn = data.get("fileName") or data.get("file") or data.get("path") or data.get("filename") or data.get("fileName") or ""
            if fn:
                return Path(fn).name
            # fallback: consider image element as sticker without filename -> use generic
            return None
    # 2. resources: type == image
    for r in msg.get("resources", []):
        if r.get("type") == "image":
            lp = r.get("local_path") or r.get("path") or ""
            if lp:
                return Path(lp).name
    # 3. explicit sticker field
    if msg.get("sticker"):
        return Path(msg["sticker"]).name
    if msg.get("sticker_id"):
        return Path(msg["sticker_id"]).name
    return None

def _context_window(messages, idx, window=3):
    start = max(0, idx - window)
    return messages[start:idx]

def build_cooccurrence(messages, tags=None, window=3, top_when=5):
    """
    messages: 已按 timestamp 排序的 CleanMessage list
    tags: dict sticker_id -> {label, emotion, keywords}
    window: 上下文窗口大小 (默认 3)
    返回: dict sticker_id -> stats
    """
    messages = sorted(messages, key=lambda m: m.get("timestamp", 0) if m.get("timestamp") else 0)
    tags = tags or {}
    stats = defaultdict(lambda: {"freq": 0, "trigger_keywords": Counter(), "categories": Counter(), "examples": []})

    # 第一遍：真实 image 消息统计
    has_real = False
    for idx, msg in enumerate(messages):
        sticker_id = extract_sticker_id(msg)
        if not sticker_id:
            continue
        has_real = True
        sticker_id = Path(sticker_id).name
        ctx = _context_window(messages, idx, window)
        ctx_texts = []
        ctx_tokens = []
        for cm in ctx:
            txt = cm.get("content", {}).get("text") if "content" in cm else cm.get("text", "")
            if not txt:
                continue
            ctx_texts.append(txt)
            ctx_tokens.extend(tokenize(txt))
        # categories / emotion proxy
        for cm in ctx:
            cat = cm.get("category")
            if cat:
                stats[sticker_id]["categories"][cat] += 1
        for tok in ctx_tokens:
            stats[sticker_id]["trigger_keywords"][tok] += 1
        stats[sticker_id]["freq"] += 1
        # verbatim example
        verbatim = f"上下文：{ctx_texts} -> 工具调用：send_sticker(\"{sticker_id}\")"
        stats[sticker_id]["examples"].append({
            "context_ids": [cm.get("id") for cm in ctx],
            "context_texts": ctx_texts,
            "sticker_message_id": msg.get("id"),
            "verbatim": verbatim,
        })

    # Fallback：若无真实 sticker 消息，基于 tags keywords 启发式合成共现
    # 这在 demo 数据中很有用（原始 30 条全文本），同时保持真实数据的优先级
    if not has_real and tags:
        # 也支持 tags 为空时使用 DEFAULT_TAGS
        effective_tags = tags if tags else DEFAULT_TAGS
        if not effective_tags:
            effective_tags = DEFAULT_TAGS
        for idx, msg in enumerate(messages):
            txt = msg.get("content", {}).get("text") if "content" in msg else msg.get("text", "")
            if not txt:
                continue
            toks = set(tokenize(txt))
            # 对每个 sticker 检查是否命中其关键词
            for sticker_id, tag in effective_tags.items():
                kws = tag.get("keywords", [])
                # 命中条件：关键词出现在文本或 tokens 中
                hit = False
                for kw in kws:
                    if kw in txt or kw in toks:
                        hit = True
                        break
                if not hit:
                    continue
                # 将当前消息的上下文窗口作为触发场景（包含当前消息本身，因为合成场景中当前消息就是触发句）
                # 取 idx 前 window 条 + 当前消息
                start = max(0, idx - window + 1)
                ctx = messages[start: idx+1]
                ctx_texts = []
                ctx_tokens = []
                for cm in ctx:
                    t = cm.get("content", {}).get("text") if "content" in cm else cm.get("text", "")
                    if not t:
                        continue
                    ctx_texts.append(t)
                    ctx_tokens.extend(tokenize(t))
                for cm in ctx:
                    cat = cm.get("category")
                    if cat:
                        stats[sticker_id]["categories"][cat] += 1
                for tok in ctx_tokens:
                    stats[sticker_id]["trigger_keywords"][tok] += 1
                stats[sticker_id]["freq"] += 1
                verbatim = f"上下文：{ctx_texts} -> 工具调用：send_sticker(\"{sticker_id}\")"
                stats[sticker_id]["examples"].append({
                    "context_ids": [cm.get("id") for cm in ctx],
                    "context_texts": ctx_texts,
                    "trigger_message_id": msg.get("id"),
                    "verbatim": verbatim,
                })
    return dict(stats)

def to_rules(stats, tags=None, top_when=5, top_keywords=10, max_examples=3):
    """
    将 co-occurrence stats 转为 STICKER_LEARNING.md 规范的 rules 格式
    """
    tags = tags or {}
    rules = {}
    for sticker_id, s in stats.items():
        tag = tags.get(sticker_id, {})
        # label 优先取 tags，否则 fallback 到 DEFAULT_TAGS
        label = tag.get("label") or DEFAULT_TAGS.get(sticker_id, {}).get("label", "未知")
        # emotion 优先取 tags，否则取最常见的 category
        emotion = tag.get("emotion")
        if not emotion:
            if s["categories"]:
                emotion = s["categories"].most_common(1)[0][0]
            else:
                emotion = DEFAULT_TAGS.get(sticker_id, {}).get("emotion", "neutral")
        trigger = s["trigger_keywords"]
        # 优先 tag keywords (按共现频次排序)，再补高频触发词，过滤助词以突出语义
        tag_kws = tag.get("keywords", []) or DEFAULT_TAGS.get(sticker_id, {}).get("keywords", [])
        from .tokenizer import KEEP_PARTICLES as _KP
        # tag 命中按 trigger 计数排序
        tag_hits = [(kw, trigger.get(kw, 0)) for kw in tag_kws if trigger.get(kw, 0) > 0]
        tag_hits.sort(key=lambda x: x[1], reverse=True)
        when = [kw for kw, _ in tag_hits]
        # 补充：按 trigger 频次但跳过已在 when 中的，且助词降权
        for w, _ in trigger.most_common():
            if w in when:
                continue
            if w in _KP:
                continue
            when.append(w)
            if len(when) >= top_when:
                break
        # 若仍不足，允许助词补齐
        if len(when) < top_when:
            for w, _ in trigger.most_common():
                if w not in when:
                    when.append(w)
                    if len(when) >= top_when:
                        break
        when = when[:top_when]
        # 兜底：若仍为空则用 tag keywords
        if not when:
            when = tag_kws[:top_when]
        # freq
        freq = s["freq"]
        # examples verbatim
        examples = [e["verbatim"] for e in s["examples"][:max_examples]]
        example_details = s["examples"][:max_examples]
        rules[sticker_id] = {
            "label": label,
            "emotion": emotion,
            "freq": freq,
            "when": when,
            "trigger_keywords": dict(trigger.most_common(top_keywords)),
            "categories": dict(s["categories"]),
            "examples": examples,
            "example_details": example_details,
        }
        # 为兼容文档示例，保留精简字段
        # 同时提供 when/ freq/ label 供 merge.py 使用
    return rules

def generate(messages, tags=None, window=3):
    stats = build_cooccurrence(messages, tags=tags, window=window)
    return to_rules(stats, tags=tags)

def load_tags(tag_path):
    if tag_path and tag_path.exists():
        try:
            data = json.loads(tag_path.read_text(encoding="utf-8"))
            # 兼容 {sticker: {label,...}} 格式
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return {}

def main(messages_path=None, tags_path=None, out_path=None, window=3):
    import argparse
    from pathlib import Path as P
    ap = argparse.ArgumentParser(description="生成 sticker_rules.json (window=3)")
    ap.add_argument("--messages", default="data/recent_messages/messages.json", help="CleanMessage JSON 或 chunks 目录")
    ap.add_argument("--tags", default="data/emojis/tags.json", help="MCP tags json")
    ap.add_argument("--out", default="data/emojis/sticker_rules.json", help="输出路径")
    ap.add_argument("--window", type=int, default=3)
    args = ap.parse_args()

    base = P(__file__).parent.parent.parent
    msgs = []
    # 支持 chunks 或单文件
    chunk_dir = base / "data" / "recent_messages" / "chunks"
    if chunk_dir.exists() and list(chunk_dir.glob("*.jsonl")):
        for p in sorted(chunk_dir.glob("*.jsonl")):
            for line in open(p, encoding="utf-8"):
                if line.strip():
                    msgs.append(json.loads(line))
    else:
        mp = base / args.messages if not P(args.messages).is_absolute() else P(args.messages)
        if mp.exists():
            data = json.loads(mp.read_text(encoding="utf-8"))
            if "messages" in data:
                msgs = data["messages"]
            elif isinstance(data, list):
                msgs = data
            else:
                msgs = [data]
    tags_p = base / args.tags if not P(args.tags).is_absolute() else P(args.tags)
    tags = load_tags(tags_p)
    if not tags:
        # fallback to DEFAULT_TAGS for demo
        tags = DEFAULT_TAGS

    rules = generate(msgs, tags=tags, window=window)
    out = base / args.out if not P(args.out).is_absolute() else P(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    meta = {"generated_at": __import__("time").strftime("%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime()), "window": window, "count_messages": len(msgs), "count_stickers": len(rules)}
    output = {"meta": meta, "rules": rules, **rules, "_meta": meta}
    out.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[sticker_rules] window={window} messages={len(msgs)} stickers={len(rules)} -> {out}")
    for sid, r in rules.items():
        print(f"  {sid}: label={r['label']} freq={r['freq']} when={r['when']} examples={r['examples'][:1]}")
    return output
if __name__ == "__main__":
    main()