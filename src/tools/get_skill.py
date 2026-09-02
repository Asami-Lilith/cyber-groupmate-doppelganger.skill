"""只读获取通道"""
from pathlib import Path
def get_skill_file(name, file):
    p = Path(f"skills/immortals/{name}/{file}")
    if p.exists(): return p.read_text(encoding="utf-8")
    return ""
def get_dynamic(persona):
    p = Path("data/persona_injected.md")
    return p.read_text(encoding="utf-8") if p.exists() else ""
