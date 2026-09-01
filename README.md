# Cyber Groupmate Doppelganger.skill

> 群聊分身 · 轻量自学习 Skill
>
> 基于 `soul.skill` 人设底座 + 近期发言/高频表情包动态权重，Skill 每次被调用时运行脚本增量更新，反哺给 LLM。

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE) [![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)](docs/SETUP.md) [![Status: Planning](https://img.shields.io/badge/status-计划阶段-yellow)](PLAN.md)

## 1. 这是什么？
在群内通过机器人留档目标人物的**近期发言**与**高频表情包**，通过 MCP 对表情包语义标记，结合 `jieba` 高频词提取，在 Skill 调用时运行脚本刷新动态权重，让 Agent 越用越像真人。

**设计目标：足够简单，无需后训练（post-training），仅脚本 + Skill 自学习。**

## 2. 特性
- **自学习**：Skill 调用时自动执行 `scripts/update_recent.py`
- **轻量**：仅 jieba + 规则统计，无大模型训练
- **低耦合**：采集/处理/人设/更新单向依赖
- **表情理解**：可选 `mcp-servers/emoji-tagger` MCP 服务
- **中文优化**：jieba 分词 + 停用词过滤

## 3. 架构速览
```
[群机器人 collectors] --jsonl--> [data/recent_messages] --jieba--> [data/keywords]
[表情 collectors] --png--> [data/emojis] --MCP--> [data/emojis/tags.json]
                                    |
            [SKILL.md 被调用] --> [scripts/update_recent.py] --> [config/persona.json 动态权重]
                                    |
                            [src/persona] 合并 soul.skill + 动态权重 --> LLM
```
详见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## 4. 目录结构
```
cyber-groupmate-doppelganger.skill/
├── SKILL.md
├── README.md
├── PLAN.md
├── config/persona.json        # 人设权重配置
├── src/
│   ├── collectors/            # 采集：消息/表情拉取
│   ├── processors/            # 处理：jieba清洗统计
│   ├── persona/               # 人设：合并 soul.skill + 权重
│   └── updater/               # 更新：调度逻辑
├── mcp-servers/emoji-tagger/  # 可选 MCP 服务
├── scripts/
│   ├── update_recent.py       # ★ 核心：Skill 触发时执行
│   └── extract_keywords.py
├── data/                      # 运行时数据（不提交）
├── tests/  docs/
```

## 5. 快速开始
```bash
git clone https://github.com/<you>/cyber-groupmate-doppelganger.skill.git
cd cyber-groupmate-doppelganger.skill
brew install python@3.12
/opt/homebrew/opt/python@3.12/bin/python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config/persona.json.example config/persona.json
python scripts/update_recent.py --demo
```
详见 [docs/SETUP.md](docs/SETUP.md)

## 6. 项目进度

> **当前进度：计划阶段 (Planning)** — 架构与文档已完成，待实现 MVP 代码。详见 [PLAN.md](PLAN.md)

## 7. 文档导航
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - 架构与耦合
- [DATA_PIPELINE.md](docs/DATA_PIPELINE.md) - 数据流水线
- [SELF_LEARNING.md](docs/SELF_LEARNING.md) - 自学习机制
- [MCP_EMOJI_TAGGER.md](docs/MCP_EMOJI_TAGGER.md) - 表情 MCP
- [SETUP.md](docs/SETUP.md) - 安装与多设备同步
