# 实施计划 - 轻量版

## 目标
无需 post-training，仅脚本 + Skill 自学习实现群聊分身。

## 模块
1. **collectors/** 消息/表情采集，写入 data/
2. **processors/** jieba 高频词提取
3. **mcp-servers/emoji-tagger** 可选，表情语义标记
4. **scripts/update_recent.py** 核心，Skill 调用时增量更新
5. **persona/** 合并 soul.skill + 动态权重

## 阶段
- Phase 1 MVP：collectors(模拟) + processors + update_recent.py
- Phase 2 动态权重：权重融合与时间衰减
- Phase 3 MCP：表情标记接入
- Phase 4 开源：docs + tests
