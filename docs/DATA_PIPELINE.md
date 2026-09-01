# 数据流水线

## 文件格式约定

### 1. recent_messages/messages.jsonl
每行一条 JSON：
```json
{"user_id": "target123", "timestamp": "2025-09-01T10:00:00Z", "text": "今天好累哈哈", "emojis": ["smile.png"]}
```
- 增量追加，脚本通过 timestamp 去重

### 2. keywords/high_freq.json
```json
{
  "哈哈": 42,
  "摸鱼": 18,
  "破防": 12
}
```
由 `scripts/extract_keywords.py` 调用 jieba 产生，Top20 + 停用词过滤。

### 3. emojis/tags.json
```json
{
  "cry_laugh.png": {"label": "笑哭", "emotion": "joy", "score": 0.9},
  "dog_head.png": {"label": "狗头保命", "emotion": "teasing", "score": 0.85}
}
```
由 MCP Server 产出。

## 处理步骤
1. **清洗**：去 @、链接、系统消息
2. **分词**：jieba.lcut，过滤长度1、标点、停用词表 `config/stopwords.txt`
3. **统计**：Counter + 时间衰减（近7天权重 x1.0，30天 x0.5）
4. **输出**：写入 high_freq.json，供 persona 合并
