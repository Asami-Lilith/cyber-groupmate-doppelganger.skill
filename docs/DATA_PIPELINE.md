# 数据流水线 - 兼容 qq-chat-exporter JSON

## 存储格式（对齐 qq-chat-exporter CleanMessage）

我们直接复用 shuakami/qq-chat-exporter 的 CleanMessage 结构（见 /tmp/qq-chat-exporter-ref/qq-chat-export-core/src/types.rs），便于用其工具导出后无缝读取。

### 单条消息
```json
{
  "id": "7000000000000000001",
  "timestamp": 1751698800000,
  "time": "2025-07-05 09:00:00",
  "sender": {"uid": "u_target123", "uin": "123456789", "name": "目标人物"},
  "messageType": "normal",
  "content": {"text": "今天好累哈哈", "elements": [{"type": "text", "data": {"text": "今天好累哈哈"}}]}
}
```
表情/图片通过 elements 区分：face/image，对应 resources + 本地 data/emojis/*.png

### 文件组织
- 单文件：data/recent_messages/messages.json {metadata, chatInfo, statistics, messages}
- 流式：data/recent_messages/chunks/c000001.jsonl 每行一个 CleanMessage + manifest.json
- 脚本同时支持两种，优先 jsonl

### 参考
- 本地：/tmp/qq-chat-exporter-ref (--depth 1)
- 核心：qq-chat-export-core/src/types.rs

## 处理步骤
1. 读取 qq-chat-exporter 导出的 JSON/JSONL
2. 清洗过滤 system 消息
3. 对 content.text 用 jieba 分词
4. 统计 -> data/keywords/high_freq.json
5. 收集 image/face -> data/emojis/

## 身份映射（QQ官方Bot限制）

官方 Bot API 返回的是 `openID`（非真实QQ号），同一用户在不同群的 openID 不同，需配置映射：

- 配置文件：`config/uid_mapping.json`（复制 .example 后填写）
- 格式：`{"groups": {"<群ID>": {"<openID>": "目标人物"}}}`
- 采集时：collectors 保留原始 `sender.uid=openID`，同时通过映射表解析 `sender.name`
- 存储时：仍按 CleanMessage 存 `uid=openID`，保证可回溯，显示名走映射
