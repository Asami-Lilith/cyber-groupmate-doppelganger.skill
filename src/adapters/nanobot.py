"""适配 nanobot history JSONL -> CleanMessage"""
import re, json, pathlib
TIME_RE = re.compile(r"^\[\d{4}-\d{2}-\d{2}.*?\]\s*")
USER_RE = re.compile(r"^\[用户=[0-9a-fA-F]{8,}\]\s*")
AT_RE = re.compile(r"<@[^>]+>")
FACE_RE = re.compile(r'<faceType=\d+,faceId="(\d+)"[^>]*>')
OPENID_RE = re.compile(r"[0-9a-fA-F]{32,}")
SYSTEM_RE = re.compile(r"【休眠期间.*?】|【记忆.*?"]", re.DOTALL)

def clean_text(raw: str):
    t = raw or ""
    # 剔除系统汇总块
    if "【休眠期间" in t or "【记忆" in t:
        return "", []
    faces = FACE_RE.findall(t)
    # 剥表情标签，不转文字
    t = FACE_RE.sub("", t)
    t = TIME_RE.sub("", t)
    t = USER_RE.sub("", t)
    t = AT_RE.sub("", t)
    # 剥残留 openid
    t = OPENID_RE.sub("", t)
    t = t.strip()
    return t, faces

def parse_line(obj: dict):
    # nanobot history: {role, content, t, user, media}
    content = obj.get("content", "")
    text, faces = clean_text(content)
    return {
        "id": obj.get("mid") or str(obj.get("t", "")),
        "timestamp": obj.get("t", 0),
        "sender": {"uid": obj.get("user", ""), "name": obj.get("user", "")[:8]},
        "content": {"text": text, "elements": []},
        "faces": faces,
        "media": obj.get("media", []),
        "raw": obj
    }
