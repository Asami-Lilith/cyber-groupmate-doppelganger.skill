# 成品阶段：Prompt 权重注入方案

## 目标
让近期发言 Skill 的动态数据获得更高权重，覆盖 immortal-skill 底座的过时表达。

## 注入时机
`SKILL.md: on_call: python scripts/update_recent.py && python src/persona/merge.py` 
→ 每次 Skill 被调用时，先刷新数据，再生成 `data/persona_injected.md`，由 Agent 将其作为 System Prompt 注入。

## 权重设计（config/persona.json）
```json
{
  "dynamic_weights": {
    "recent_messages_weight": 0.6,
    "emoji_weight": 0.3,
    "base_persona_weight": 0.1
  }
}
```
0.6 : 0.3 : 0.1 保证近期发言主导，表情为辅，底座仅保留基础性格。

## 注入模板（src/persona/merge.py 生成）
1. **基础人设区** 标注权重 0.1
2. **近期动态区** 标注【高优先级，冲突时以此为准】，权重 0.6，包含：
   - 高频词 Top10（jieba 产出）
   - 典型句式（最近5条原话）
   - 明确指令："用词、口头禅必须贴近高频词"
3. **表情区** 权重 0.3，列出 tags.json 前5个表情
4. **融合规则** 显式告诉 LLM：近期 > 基础，不要暴露权重逻辑

## 为何有效？
- LLM 对 System Prompt 中显式"优先级""权重"指令敏感
- 不塞全量历史，只塞总结（20词），不占 attention，权重更集中
- 脚本在 Skill 调用时同步执行，保证动态数据最新

## 扩展
- 如需更强权重，可将动态区放在 Prompt 最末（LLM 更关注末尾）
- 或将权重改为 0.7/0.2/0.1
