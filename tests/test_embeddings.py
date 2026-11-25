import sys

import numpy as np
from src.embeddings import Embedder
from src.similarity import cosine_matrix

PARAPHRASE = "Neighbors in Alderwick created a shared garden and rotated watering duties every week."
RELATED = "Alderwick residents established a community garden and divided weekly irrigation work."
UNRELATED = "Quantum chromodynamics describes quarks, gluons, and particle interactions."


def test_primary_model_dimensions_and_paraphrase_ranking():
    embedder = Embedder(device="cpu")
    if embedder.fallback:
        import pytest
        pytest.skip(f"primary model could not load: {embedder.failure_reason}")
    vectors = embedder.encode([PARAPHRASE, RELATED, UNRELATED])
    assert vectors.shape == (3, 384)
    scores = cosine_matrix(vectors)
    assert scores[0, 1] > scores[0, 2]
    assert embedder.backend == "sentence-transformers/all-MiniLM-L6-v2"


def test_tfidf_fallback_is_labeled_and_ranks_shared_language(monkeypatch):
    monkeypatch.setitem(sys.modules, "sentence_transformers", None)
    embedder = Embedder(device="cpu")
    vectors = embedder.encode([PARAPHRASE, RELATED, UNRELATED, "!!! ???"])
    scores = cosine_matrix(vectors)
    assert vectors.shape[0] == 4
    assert embedder.fallback
    assert "TF-IDF" in embedder.backend
    assert "not semantic" in embedder.backend or "lexical-only" in embedder.backend
    assert scores[0, 1] > scores[0, 2]
