# 自学习机制（无训练）

## 触发
- **主触发**：Skill 每次被调用时执行 `scripts/update_recent.py`
- **可选**：定时任务 `*/30 * * * * python scripts/update_recent.py`

## 权重融合
`config/persona.json`：
```json
{
  "base": "immortal-skill",
  "dynamic_weights": {
    "recent_messages_weight": 0.45,
    "emoji_weight": 0.25,
    "base_persona_weight": 0.30
  },
  "decay": {"half_life_days": 7}
}
```
最终 Prompt = base_persona *0.30 + 近期高频词/句式 *0.45 + 表情偏好 *0.25
7 天前发言权重减半，避免过时口头禅残留。

## 为何脚本足够？
不把全量历史塞进 Prompt，而是离线总结成 `high_freq.json`（20词 + 5典型句式），调用时只注入总结，节省 attention，且无需任何模型训练。
