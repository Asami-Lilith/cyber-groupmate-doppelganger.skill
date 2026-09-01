# MCP Emoji Tagger (Image Sticker)

## 契约
- 输入: tag_emoji(image_path: str) -> {label, emotion, keywords, score}
- 输入: send_sticker(image_path, context) -> {action: send, image}
- 输出: data/emojis/tags.json {filename: {label, emotion, keywords, score}}
- 输出: data/emojis/sticker_rules.json {filename: {when:[str], examples:[str], freq}}

## 实现
- 规则桩：文件名含 dog/cry 即打标签，实际可接 CLIP
- 进程隔离，通过 MCP 调用
