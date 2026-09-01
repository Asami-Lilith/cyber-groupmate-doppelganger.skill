#!/usr/bin/env python3
"""MCP Server 雏形：图片表情包标记 + 工具调用"""
import json
from pathlib import Path
# 轻量规则：文件名含关键词即打标签，实际可接 CLIP/视觉模型
TAG_RULES = {
    "dog": {"label":"狗头","emotion":"teasing"},
    "cry": {"label":"笑哭","emotion":"joy"},
    "angry": {"label":"生气","emotion":"anger"},
}

def tag_image(path: str):
    name = Path(path).name.lower()
    for k,v in TAG_RULES.items():
        if k in name:
            return {**v, "keywords":["破防","离谱"] if k=="dog" else ["哈哈"]}
    return {"label":"通用","emotion":"neutral","keywords":[]}

# MCP 工具定义（示意）
TOOLS = {
    "tag_emoji": tag_image,
    "send_sticker": lambda path: {"action":"send", "image": path}
}

if __name__=="__main__":
    print("MCP emoji-tagger ready, tools:", list(TOOLS.keys()))
