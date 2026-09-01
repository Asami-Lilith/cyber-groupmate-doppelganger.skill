# 需求清单 - 仅 Skill + 脚本（不含真实机器人）

> 基准：轻量、无训练、同步执行、中文群聊特化

## Must (本期必须实现)
1. **Skill 骨架**
   - `SKILL.md` (<100行) 触发 `scripts/update_recent.py && src/persona/merge.py` → 生成 `data/persona_injected.md`
   - `config/immortal.base.md` + `config/persona.json` 权重 0.45/0.25/0.30 + 时间衰减 7天
2. **数据兼容**
   - 输入：`qq-chat-exporter` CleanMessage JSON（单文件/ chunked jsonl 均兼容）
   - 存储：`data/recent_messages/messages.json`, `data/emojis/*.png`
   - 映射：`config/uid_mapping.json` <群,openID> -> 展示名（QQ官方 Bot限制）
3. **中文处理**
   - `src/processors/extractors.py`：jieba + 自定义词典(yyds/破防/摸鱼) + 保留助词(啊/呢/吧/嘛/哈)
   - 4档提取：counter / tfidf(时间衰减) / yake / textrank(window=2) 可通过 --method 切换，默认 yake
4. **自学习脚本**
   - `scripts/update_recent.py --demo` 生成示例，`--method` 切换，产出 `data/keywords/high_freq.json` (Top20)
   - 双轨：style(助词) + hot(近7天热点) 分别统计，供 merge.py 注入
5. **人设合并**
   - `src/persona/merge.py` 合并 immortal-skill 底座 + 动态权重，生成 `persona_injected.md` 仅含 Top15 + 3条 verbatim，不贴120条原文
6. **图片表情包（工具调用）**
   - `mcp-servers/emoji-tagger/server.py` 标记 + `data/emojis/sticker_rules.json` 上下文共现（前3条消息）→ 注入规则 `when:[破防,离谱] -> send_sticker("dog_head.png")`
7. **文档与学术**
   - `README` 含项目边界说明，`docs/` 含 ARCHITECTURE/DATA_PIPELINE/PROMPT_INJECTION/STICKER_LEARNING/LITERATURE(2)/METHODOLOGY

## Should (本期尽量)
- `tests/` 对 extractors 的单元测试（120条用例已验证）
- `config/uid_mapping.json.example` + `data` 示例

## Out of Scope (本期不做)
- 真实 QQ/Discord/飞书 Bot 接入（由使用者按接口自写）
- 模型后训练/微调（Qwen LoRA）
- 提示词的平台个性化（由使用者按需改）

## 验收标准
- `python scripts/update_recent.py --demo && python src/persona/merge.py` 在 <1s 内生成 `high_freq.json` 且助词置顶
- `data/persona_injected.md` < 2KB，仅含摘要+3条 verbatim
- `git push` 后可在新设备 `pip install -r requirements.txt` 后复现
