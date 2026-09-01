---
name: cyber-groupmate-doppelganger
version: 0.1.0
description: 群聊分身，轻量自学习（脚本增量更新近期发言与表情）
triggers:
  - on_call: "python scripts/update_recent.py && python src/persona/merge.py"
---

# Cyber Groupmate Doppelganger

轻量 Skill：每次被调用时依次执行：
1. `scripts/update_recent.py` 增量更新近期发言与表情 -> `data/keywords/high_freq.json`
2. `src/persona/merge.py` 合并 immortal-skill 底座 + 动态权重 -> `data/persona_injected.md`

Agent 将 `data/persona_injected.md` 作为 System Prompt 注入，权重以 `config/persona.json` 为唯一真值（近期 > 表情 > 底座）。
