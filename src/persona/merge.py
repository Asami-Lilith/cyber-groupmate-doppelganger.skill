#!/usr/bin/env python3
"""
成品阶段：合并 immortal-skill 底座 + 近期动态权重，生成最终注入 Prompt
权重通过 config/persona.json 配置，无需改代码
"""
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
CONFIG = BASE_DIR / "config" / "persona.json"
DATA_KW = BASE_DIR / "data" / "keywords" / "high_freq.json"
DATA_EMOJI = BASE_DIR / "data" / "emojis" / "tags.json"
BASE_FILE = BASE_DIR / "config" / "immortal.base.md"  # immortal-skill 底座文本
OUT = BASE_DIR / "data" / "persona_injected.md"

def load_base():
    if BASE_FILE.exists():
        return BASE_FILE.read_text(encoding="utf-8")
    return "# 基础人设\n你是一个友善的群友，性格开朗。"

def main():
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    w = cfg.get("dynamic_weights", {})
    w_recent = w.get("recent_messages_weight", 0.6)
    w_emoji = w.get("emoji_weight", 0.3)
    w_base = w.get("base_persona_weight", 0.1)

    kws = {}
    if DATA_KW.exists():
        kws = json.loads(DATA_KW.read_text(encoding="utf-8"))
    top_words = ", ".join(list(kws.keys())[:10]) if kws else "暂无"

    emoji_tags = {}
    if DATA_EMOJI.exists():
        emoji_tags = json.loads(DATA_EMOJI.read_text(encoding="utf-8"))
    emoji_desc = ", ".join([f"{k}({v.get('label','')})" for k,v in list(emoji_tags.items())[:5]]) if emoji_tags else "暂无"

    soul = load_base()

    # 五档映射：权重→措辞/数量/位置（新增两档，更平滑）
    # L5 MUST(0.4+) Top10末端, L4 SHOULD(0.25-0.4) Top5, L3 RECOMMENDED(0.15-0.25) Top3, L2 MAY(0.05-0.15) 1-2条, L1 OPTIONAL 1句
    def degree(w):
        if w >= 0.4: return ("必须", 10, "末端")
        if w >= 0.25: return ("应该", 5, "中部")
        if w >= 0.15: return ("建议", 3, "中部")
        if w >= 0.05: return ("可", 2, "附录")
        return ("仅参考", 1, "开头")
    d_recent, recent_n, pos_recent = degree(w_recent)
    d_base, base_n, pos_base = degree(w_base)
    d_emoji, emoji_n, pos_emoji = degree(w_emoji)
    prompt = f"""# Persona Injection - Cyber Groupmate Doppelganger

## 1. 基础人设 (immortal-skill) - {d_base}参考（{pos_base}）
{soul[:300]}

## 2. 近期动态 【{d_recent}优先模仿，冲突时以此为准】
### 高频词（Top{recent_n}，{d_recent}自然融入）：
{top_words}
### 典型句式：参考近期5条原话（已衰减）
### 指令：{d_recent}贴近上述高频词；优先级高于底座。

## 3. 表情包工具 【{d_emoji}调用】
{emoji_desc and f"可用表情（Top{emoji_n}）：{emoji_desc}。{d_emoji}调用 send_sticker" or "暂无"}

## 4. 融合规则
- 近期 > 表情 > 底座（{d_recent}>{d_emoji}>{d_base}）
- {d_recent}级不可违背，其余可权衡
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(prompt, encoding="utf-8")
    print(f"已生成注入 Prompt -> {OUT}")
    print(prompt[:800])

if __name__ == "__main__":
    main()
