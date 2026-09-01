---
name: cyber-groupmate-doppelganger
version: 0.1.0
description: 群聊分身，轻量自学习（脚本增量更新近期发言与表情）
triggers:
  - on_call: "python scripts/update_recent.py"
---

# Cyber Groupmate Doppelganger

轻量 Skill：每次被调用时触发 `scripts/update_recent.py`，增量更新近期发言与表情数据，融合到人设中。无需模型训练。
