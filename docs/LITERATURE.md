# 学术支撑

> 免费接口来源：Crossref（按被引量）+ arXiv（按时效），均可在谷歌学术验证

## 1. 关键词提取（对应 scripts/update_recent.py）
- **Mihalcea & Tarau. TextRank: Bringing Order into Texts. EMNLP 2004** 被引 8000+ — 原版图排序无监督关键词提取，谷歌学术搜 `TextRank EMNLP 2004`
- **Automatic Text Summarization Method Based on Improved TextRank Algorithm and K-Means. Knowledge-Based Systems 2024.11** 被引 51 — Crossref 2024 高被引改进版，DOI:10.1016/j.knosys.2024.111447
- **Extractive Article Summarization Using Integrated TextRank and BM25+. Electronics 2023** 被引 36 — DOI:10.3390/electronics12020372
- **Števaňák et al. SlovKE: Large-Scale Dataset and LLM Evaluation for Slovak Keyphrase Extraction. arXiv:2603.15523 (2026-03-16, LREC 2026)** — 对比 YAKE/TextRank/KeyBERT，证明 TextRank 在变形语言上仅 11.6% F1，支撑我们升级到 KeyBERT
- **Campos et al. YAKE! Unsupervised Keyword Extraction. 2020** / **Grootendorst KeyBERT 2020** — 轻量无监督，适合离线20词总结

## 2. 中文分词（对应 src/processors jieba）
- **Liu et al. Neural Chinese Word Segmentation with Dictionary Knowledge. NLPCC 2018 (arXiv:1807.05849)** — 前缀词典+HMM 正是 jieba 原理，证明词典在小数据有效
- **Zhao et al. Chinese Word Segmentation: Another Decade Review (2007-2017). arXiv:1901.06079** — 十年综述，结论：词典+统计在短文本不输神经网络，支撑轻量方案

## 3. 表情（可选，权重已降至0.10）
- 仅保留 emoji2vec/DeepMoji 作参考，本项目重心为中文文本

## 4. 人设/风格（对应 src/persona/merge.py 权重注入）
- **Zhang et al. Persona-Chat. 2018** — 人格一致性评测标准
- **Brown et al. Language Models are Few-Shot Learners (GPT-3). NeurIPS 2020** — 证明 Prompt 注入高频示例即可改变风格，支撑 `recent 0.45 > base 0.30` 的 In-Context 权重

## 与本项目映射
- 中文分词 → src/processors (jieba + HMM)
- 关键词提取 → scripts/update_recent.py (Counter → TF-IDF/TextRank/KeyBERT)
- 表情理解 → mcp-servers/emoji-tagger (emoji2vec)
- 权重注入 → src/persona/merge.py (In-Context Learning)
