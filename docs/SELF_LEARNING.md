# 自学习与动态权重执行（不让 LLM 算数）

> 关键：权重 0.45/0.25/0.30 是给**脚本**看的，不是给 LLM 看的。LLM 只看到自然语言优先级。

## 权重如何执行
1. **数量**：权重 → 注入词数。0.45 → Top10 高频词，0.30 → 底座仅保留 3 句兜底，0.25 → 表情包最多 5 条规则
2. **位置**：近期动态放在 Prompt 末端（LLM 更关注末尾），底座放开头作兜底
3. **措辞**：翻译为 “【高优先级，冲突时以此为准，必须优先模仿】” 而非 “权重0.45”
4. **时间**：时间衰减已在 high_freq.json 中完成（近7天 x1.0，旧数据 x0.6），LLM 无需计算时间

## 触发
- `SKILL.md: on_call: python scripts/update_recent.py && python src/persona/merge.py` — 每次调用时脚本先算好权重对应的数量与优先级，再生成 `data/persona_injected.md`
- LLM 仅读取生成的自然语言规则，无需量化

## 与 immortal-skill 一致
- 采用证据分级 `verbatim > artifact > impression`，而非数字权重；我们的“近期动态”即高优先级 verbatim。
