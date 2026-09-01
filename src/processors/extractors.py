"""Facade for backward compatibility - split into tokenizer.py + scorers.py"""
from .tokenizer import tokenize, KEEP_PARTICLES, STOPWORDS
from .scorers import counter_keywords, tfidf_keywords, yake_keywords, textrank_keywords
