import jieba
try:
    for w in ["yyds","破防","摸鱼","确实","哈哈"]:
        jieba.add_word(w, freq=100000)
    HAS_JIEBA=True
except ImportError:
    HAS_JIEBA=False

KEEP_PARTICLES = {"啊","呢","吧","嘛","哈","呀","哦","哇","呐"}
STOPWORDS = {"的","了","是","在","和","与","就","都","而","及","着","，","。","、","！","？"," ","\n"}

def tokenize(text):
    if not HAS_JIEBA:
        return [c for c in text if c.strip() and c not in STOPWORDS]
    toks = jieba.lcut(text)
    out=[]
    for w in toks:
        if not w.strip(): continue
        if w in STOPWORDS: continue
        if w in KEEP_PARTICLES:
            out.append(w); continue
        if len(w)==1 and w not in KEEP_PARTICLES: continue
        out.append(w)
    return out
