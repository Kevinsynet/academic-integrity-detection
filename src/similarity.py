"""Dense vector and supplementary lexical similarity helpers."""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def cosine_matrix(vectors):
    """Return the exact cosine matrix for a two-dimensional vector array."""
    values = np.asarray(vectors, dtype=np.float32)
    if values.ndim != 2:
        return np.zeros((0, 0), dtype=np.float32)
    norms = np.linalg.norm(values, axis=1, keepdims=True)
    normalized = values / np.maximum(norms, 1e-12)
    return normalized @ normalized.T


def lexical_score(left, right):
    """Calculate pairwise TF-IDF cosine as a supplementary lexical signal."""
    if not left.strip() or not right.strip():
        return 0.0
    try:
        vectors = TfidfVectorizer(ngram_range=(1, 2)).fit_transform([left, right])
    except ValueError:
        return 0.0
    return float(cosine_similarity(vectors)[0, 1])
