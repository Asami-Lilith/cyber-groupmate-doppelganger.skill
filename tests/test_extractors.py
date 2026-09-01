import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.processors.tokenizer import tokenize
from src.processors.scorers import counter_keywords

def test_tokenize_keep_particles():
    assert "啊" in tokenize("今天好累啊哈哈")
    assert "呢" in tokenize("破防了呢")
    print("test_tokenize_keep_particles passed")

def test_custom_word():
    toks = tokenize("确实 yyds 摸鱼")
    assert "yyds" in toks and "摸鱼" in toks
    print("test_custom_word passed")

def test_empty_fallback():
    assert counter_keywords([], top_k=5) == []
    print("test_empty passed")

if __name__=="__main__":
    test_tokenize_keep_particles()
    test_custom_word()
    test_empty_fallback()
    print("all tests passed")
