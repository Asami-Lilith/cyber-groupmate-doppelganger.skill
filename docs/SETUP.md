# 安装与多设备同步

## 要求
- Python 3.12+
- 依赖仅 `jieba` + `mcp`（可选）

## 1. 安装 Python
```bash
brew install python@3.12
```

## 2. 克隆与环境
```bash
git clone https://github.com/<you>/cyber-groupmate-doppelganger.skill.git
cd cyber-groupmate-doppelganger.skill
/opt/homebrew/opt/python@3.12/bin/python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. 配置
```bash
cp config/persona.json.example config/persona.json
# 填入 immortal-skill 人设与 target_user_id
```

## 4. 验证（无需真实群）
```bash
python scripts/update_recent.py --demo
cat data/keywords/high_freq.json
pytest tests/ -v
```

## 5. 多设备同步
- 提交：`src/`, `scripts/`, `config/*.example`, `docs/`, `SKILL.md`
- 不提交：`data/`, `.venv/`, `config/*.json`
