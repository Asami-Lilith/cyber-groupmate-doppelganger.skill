#!/usr/bin/env python3
"""合并 immortal-skill 底座 + 近期动态权重，生成最终注入 Prompt - 权重仅给脚本看"""
import json, math, time
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).parent.parent.parent
CONFIG = BASE_DIR / "config" / "persona.json"
DATA_KW = BASE_DIR / "data" / "keywords" / "high_freq.json"
DATA_EMOJI = BASE_DIR / "data" / "emojis" / "tags.json"
DATA_MSG = BASE_DIR / "data" / "recent_messages" / "messages.json"
BASE_FILE = BASE_DIR / "config" / "immortal.base.md"
OUT = BASE_DIR / "data" / "persona_injected.md"

def load_base():
    if BASE_FILE.exists():
        return BASE_FILE.read_text(encoding="utf-8")
    return "# 基础人设\n你是一个友善的群友，性格开朗。"

def degree_with_hysteresis(w, prev=None):
    # hysteresis ±0.02 避免微扰跨档
    eps = 0.02
    if w >= 0.4 - eps:
        return ("必须", 10, "末端")
    if w >= 0.25 - eps:
        return ("应该", 5, "中部")
    if w >= 0.15 - eps:
        return ("建议", 3, "中部")
    if w >= 0.05 - eps:
        return ("可", 2, "附录")
    return ("仅参考", 1, "开头")

def main():
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    w = cfg.get("dynamic_weights", {})
    if "recent_messages_weight" not in w or "emoji_weight" not in w or "base_persona_weight" not in w:
        raise ValueError("config/persona.json 缺少权重字段，以该文件为唯一真值")
    w_recent = w["recent_messages_weight"]
    w_emoji = w["emoji_weight"]
    w_base = w["base_persona_weight"]
    half_life = cfg.get("decay", {}).get("half_life_days", 7)

    kws = {}
    if DATA_KW.exists():
        kws = json.loads(DATA_KW.read_text(encoding="utf-8"))
    # 时间衰减已在 extractors 中用 timestamp 指数衰减，此处仅展示已衰减结果
    top_words = ", ".join(list(kws.keys())[:10]) if kws else "暂无"

    emoji_tags = {}
    if DATA_EMOJI.exists():
        try:
            emoji_tags = json.loads(DATA_EMOJI.read_text(encoding="utf-8"))
        except:
            emoji_tags = {}
    # 空集降级：无表情时降为 L1
    if not emoji_tags:
        d_emoji, emoji_n, pos_emoji = ("仅参考", 1, "开头")
        emoji_desc = "暂无，跳过调用"
    else:
        # 五档映射
        def deg(w):
            if w >= 0.4: return ("必须", 10, "末端")
            if w >= 0.25: return ("应该", 5, "中部")
            if w >= 0.15: return ("建议", 3, "中部")
            if w >= 0.05: return ("可", 2, "附录")
            return ("仅参考", 1, "开头")
        d_emoji, emoji_n, pos_emoji = deg(w_emoji)
        emoji_desc = ", ".join([f"{k}({v.get('label','')})" for k,v in list(emoji_tags.items())[:emoji_n]]) if emoji_tags else "暂无，跳过调用"
        if not emoji_desc:
            emoji_desc = "暂无，跳过调用"
    # 五档映射 for recent/base
    def deg2(w):
        if w >= 0.4: return ("必须", 10, "末端")
        if w >= 0.25: return ("应该", 5, "中部")
        if w >= 0.15: return ("建议", 3, "中部")
        if w >= 0.05: return ("可", 2, "附录")
        return ("仅参考", 1, "开头")
    d_recent, recent_n, pos_recent = deg2(w_recent)
    d_base, base_n, pos_base = deg2(w_base)
    soul = load_base()
    # 位置兑现：近期高权重时放末端（LLM 更关注末尾）
    if w_recent >= 0.4:
        prompt = f"""# Persona Injection

## 1. 基础人设 (immortal-skill) - {d_base}参考（{pos_base}）
{soul[:300]}

## 2. 表情包工具 【{d_emoji}调用】
{emoji_desc}

## 3. 近期动态 【{d_recent}优先模仿，冲突时以此为准】 - 置于末端
### 高频词（Top{recent_n}，{d_recent}自然融入）：
{top_words}
### 指令：{d_recent}贴近上述高频词；优先级高于底座。

## 4. 融合规则
- 近期 > 表情 > 底座（{d_recent}>{d_emoji}>{d_base}）
- {d_recent}级不可违背，其余可权衡
"""
    else:
        prompt = f"""# Persona Injection

## 1. 基础人设 (immortal-skill) - {d_base}参考（{pos_base}）
{soul[:300]}

## 2. 近期动态 【{d_recent}优先模仿】
### 高频词（Top{recent_n}）：
{top_words}

## 3. 表情包工具 【{d_emoji}调用】
{emoji_desc}
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(prompt, encoding="utf-8")
    print(f"已生成注入 Prompt -> {OUT}")
    print(prompt[:600])

if __name__ == "__main__":
    main()
