import math
from collections import Counter, defaultdict
from .tokenizer import tokenize

def counter_keywords(messages, top_k=20):
    words=[]
    for m in messages:
        t=m["content"]["text"] if "content" in m else m.get("text","")
        words.extend(tokenize(t))
    return Counter(words).most_common(top_k)

def tfidf_keywords(messages, top_k=20, half_life_days=7):
    import time
    N=len(messages)
    docs=[tokenize(m["content"]["text"] if "content" in m else m.get("text","")) for m in messages]
    df=Counter()
    for d in docs:
        for w in set(d): df[w]+=1
    now = max([m.get("timestamp", 0) for m in messages] + [int(time.time()*1000)])
    scores=defaultdict(float)
    for idx, d in enumerate(docs):
        ts = messages[idx].get("timestamp", now)
        days_ago = (now - ts) / (1000*3600*24) if ts else 0
        decay = 0.5 ** (days_ago / half_life_days) if half_life_days else 1.0
        if not messages[idx].get("timestamp"):
            decay = 1.0 if idx >= N*0.7 else 0.6
        cnt=Counter(d)
        total=len(d) or 1
        for w,c in cnt.items():
            tf=c/total
            idf=math.log(N/(df[w] or 1) + 1)
            scores[w]+= tf*idf*decay
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

def yake_keywords(messages, top_k=20):
    words=[]
    for m in messages:
        t=m["content"]["text"] if "content" in m else m.get("text","")
        words.extend(tokenize(t))
    cnt=Counter(words)
    from .tokenizer import KEEP_PARTICLES
    scores={w: c/len(words)*(1.5 if w in KEEP_PARTICLES else 1.0) for w,c in cnt.items()} if words else {}
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

def textrank_keywords(messages, top_k=20, window=2):
    toks_list=[tokenize(m["content"]["text"] if "content" in m else m.get("text","")) for m in messages]
    vocab=list(set(w for toks in toks_list for w in toks))
    if not vocab: return []
    graph=defaultdict(dict)
    for toks in toks_list:
        for i,w in enumerate(toks):
            for j in range(i+1, min(i+window+1, len(toks))):
                u,v=w,toks[j]
                if u==v: continue
                graph[u][v]=graph[u].get(v,0)+1
                graph[v][u]=graph[v].get(u,0)+1
    scores={w:1.0 for w in vocab}
    d=0.85
    for _ in range(20):
        new={}
        for w in vocab:
            s=sum(graph[w].get(nb,0)/ (sum(graph[nb].values()) or 1) * scores[nb] for nb in graph[w])
            new[w]=(1-d)+d*s
        scores=new
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
