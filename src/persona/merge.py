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

    # 权重不直接给 LLM 看数字，而是翻译为：数量/位置/优先级措辞
    recent_n = int(10 * w_recent / 0.45) if w_recent else 8  # 0.45->10词, 按比例
    base_n = 3 if w_base < 0.4 else 5
    prompt = f"""# Persona Injection - Cyber Groupmate Doppelganger

## 1. 基础人设 (immortal-skill) - 兜底参考
{soul}

## 2. 近期动态 【高优先级，冲突时以此为准，必须优先模仿】
### 高频词（Top{recent_n}，必须自然融入回答，不要堆砌）：
{top_words}
### 典型句式：参考 data/recent_messages 中最近5条原话的句式（已按时间衰减）
### 指令：你的用词、口头禅、缩写必须贴近上述高频词；近期动态的优先级明显高于基础人设。

## 3. 表情包工具
{emoji_desc and f"可用表情：{emoji_desc}。合适时可调用 send_sticker" or "暂无表情包规则"}

## 4. 融合规则
- 近期动态优先于基础人设，遇矛盾以近期为准
- 不要提及模仿或权重，保持自然
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(prompt, encoding="utf-8")
    print(f"已生成注入 Prompt -> {OUT}")
    print(prompt[:800])

if __name__ == "__main__":
    main()
