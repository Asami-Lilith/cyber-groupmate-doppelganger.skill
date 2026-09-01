# 表情包（图片）学习 - 何时发哪张图

> 目标：让 AI 学会在恰当情景调用 `send_sticker(image)` 工具，发送原身常用的那张图片（非 emoji）

## 1. 数据（已对齐 qq-chat-exporter）
- `data/emojis/*.png` — 原身发送的表情包原图（collectors 采集）
- `data/recent_messages/messages.json` — CleanMessage 中 `elements: [{"type":"image","data":{"fileName":"xxx.png"}}]` + `resources: [{type:"image", local_path:"data/emojis/xxx.png"}]`
- 上下文窗口：每张表情包前 N=3 条消息作为触发场景

## 2. 学习（轻量统计，无训练）
- **MCP 标记**：`mcp-servers/emoji-tagger` 对每张图打标签 `{"label":"笑哭狗头","emotion":"teasing","keywords":["破防","离谱"]}`
- **共现统计**：统计 `sticker_id -> {trigger_keywords: Counter, emotion: Counter, freq}`
  - 例：`dog_head.png` 在含“破防/离谱”时出现 5次，在“安慰”场景 3次
- **产出**：`data/emojis/sticker_rules.json`
```json
{
  "dog_head.png": {"label":"狗头保命","when":["破防","离谱","玩笑"], "examples": ["前文：破防了呢 -> 发 dog_head.png"]},
  "cry_laugh.png": {"label":"笑哭","when":["笑死","哈哈"], "freq":8}
}
```

## 3. 注入（不直接贴图，贴规则+示例）
- `src/persona/merge.py` 生成 `data/persona_injected.md` 时注入：
```
## 表情包工具 权重0.25
可用工具：send_sticker(image_path)
规则：
- 当话题含“破防/离谱”且语气为 teasing 时，可调用 send_sticker("data/emojis/dog_head.png")
示例（verbatim）：
  上下文：["破防了呢"] -> 工具调用：send_sticker("dog_head.png")
```
- 符合 immortal-skill 的 verbatim 证据分级：示例标注来源 id，可追溯

## 4. 工具调用
- MCP 定义 `send_sticker`，Agent 根据规则自主决定是否调用，不强制每次都发
- 评估：统计“应发而未发/误发"，可离线对比原身真实使用频率

## 5. 与权重
- 近期发言 0.45 / 表情包规则 0.25 / 底座 0.30（表情包权重已回调，因是图片需显式规则）
