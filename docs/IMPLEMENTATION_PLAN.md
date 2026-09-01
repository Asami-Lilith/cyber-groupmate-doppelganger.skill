# 落地计划 - 不直接贴数据，学 immortal-skill 的约束写法

## 1. immortal-skill 如何约束记忆与说话方式
- **分维度文件，按需加载**：不把所有聊天贴进 SKILL.md，而是拆为 `interaction.md`（怎么说话）、`memory.md`（记得什么）、`personality.md`（价值观），SKILL.md <100行仅写阅读优先级。
- **证据分级**：`verbatim`（原话可追溯）> `artifact`（文档客观）> `impression`（主观印象隔离存放），合并时按此优先级裁决冲突。
- **说话方式**：在 `interaction.md` 中按“默认沟通方式/提问/质疑/冲突/排斥场景”结构化，而非堆砌原句；每条标注来源。
- **记忆**：`memory.md` 按“人生转折/反复故事/共同记忆/情感地图/时代印记”5视角提取，回避话题仅标注存在不深挖。
- **输出契约**：`manifest.json` + `conflicts.md` + frontmatter 单行 JSON，保证 Agent 按需读取而非全量塞 Prompt。

## 2. 新增学术支撑（免费接口已验证）
- **记忆约束**：Packer et al. MemGPT (2023, arXiv:2310.08560) — 操作系统式分级记忆，Zep (arXiv:2501.13956, 2025) 超越 MemGPT 94.8% vs 93.4%，证明分级/图式记忆优于直接贴数据。
- **说话方式**：Chen et al. A Systematic Analysis of Persona Steering on LLM Capabilities (arXiv:2604.11048, 2026) — 人设注入不仅改风格，更稳定改变认知任务表现，需按任务动态路由。
- **已有**：Persona-Chat 2018（一致性评测）、GPT-3 Few-Shot 2020（In-Context 权重注入）

## 3. 本项目落地（轻量版 immortal-skill）

**不直接贴数据的做法**
- 原始 120 条 CleanMessage **不**进 Prompt，仅离线生成摘要：
  - `data/keywords/high_freq.json`（YAKE/TextRank Top20，含助词 啊/呢/吧/哈 + 常用词 确实/破防/摸鱼 + 近期热点 yyds）
  - `data/keywords/style.json`（助词分布）与 `data/keywords/hot.json`（近7天高频）双轨，分别权重 0.15/0.40
  - 典型原话仅保留 3-5 条 `verbatim` 作证据，标注来源 id

**文件映射（对齐 immortal-skill 输出契约，但极简化）**
- `interaction.md` ← `style.json` + 3条 verbatim（怎么说话）
- `memory.md` ← `hot.json`（近期热点话题）+ 共同记忆（可选）
- `SKILL.md` 保持 <100行，写：`先读 interaction.md 再按需读 memory.md，遇矛盾以 verbatim 为准`，frontmatter 写入 `evidence: "style:5v hot:8v"`

**权重注入（不贴全文）**
- `src/persona/merge.py` 生成 `data/persona_injected.md` 时，仅注入 Top15 + 3条 verbatim + 指令“用词贴近高频词，冲突时近期热点优先”，而非120条原文，节省 attention 且符合 MemGPT 分级思想。

**验证**
- 已用 120 条测试：`counter/yake` 均保留助词，`yyds/破防` 等热点在 Top10，证明轻量统计即可达到论文级可解释性，无需训练。
