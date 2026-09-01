# MCP Emoji Tagger（可选）

## 职责
独立 MCP Server，接收表情包图片，返回简单语义标签。主 Skill 通过 MCP 调用，进程隔离，挂了不影响主链路。

## 接口（MCP Tools）
- `tag_emoji(image_path: str) -> {label, emotion, score}`
- `batch_tag(dir: str) -> tags.json`

## 实现（保持简单）
- **默认**：文件名/本地规则 + 轻量分类，无需大模型
- 表情标签写入 `data/emojis/tags.json` 供 updater 读取

## 配置
`config/mcp.json`：
```json
{
  "mcpServers": {
    "emoji-tagger": {
      "command": "python",
      "args": ["mcp-servers/emoji-tagger/server.py"]
    }
  }
}
```

## 数据流
`collectors` 存 png -> `scripts/tag_emojis.py` 调 MCP -> 写入 `data/emojis/tags.json`
