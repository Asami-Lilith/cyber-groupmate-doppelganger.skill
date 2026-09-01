# Prompt 权重注入（不给 LLM 看数字）

## 权重给脚本，不给 LLM
- `config/persona.json` 的 0.45/0.25/0.30 仅脚本 `merge.py` 读取，用于决定：注入多少词、放哪、写什么优先级措辞
- LLM 看到的是：`【高优先级，冲突时以此为准，必须优先模仿】` + Top10 高频词 + 3条 verbatim，而非“权重0.45”

## 执行映射
| 权重 | 脚本行为 | LLM 看到 |
|------|----------|-----------|
| recent 0.45 | 注入 Top10，放在 Prompt 末端 | “近期动态【高优先级】...必须优先模仿” |
| emoji 0.25 | 最多5条规则 + 3个示例 | “可用表情：...合适时可调用 send_sticker” |
| base 0.30 | 仅3句兜底，放开头 | “基础人设 - 兜底参考” |

## 注入时机
`SKILL.md: on_call: python scripts/update_recent.py && python src/persona/merge.py` → 生成 `data/persona_injected.md` → Agent 按需读取，符合 immortal-skill 的分级加载思想
