# 贡献指南

## 分支与提交
- `main` 保护，功能分支 `feat/collector-qq` / `feat/mcp-tagger`
- 提交信息：`feat: 完成 jieba 高频词衰减` / `docs: 完善 data pipeline`
- 每个模块保持低耦合，PR 需包含 `tests/test_<module>.py`

## 新增模块 checklist
1. 在 `src/<module>/` 下新建，保持无跨层 import
2. 定义输入/输出文件 Schema，写入 docs
3. 提供 `--demo` 可离线运行模式
4. 更新 `docs/ARCHITECTURE.md` 与本 README
