import numpy as np

from src.indexer import NumpyIndex
from src.similarity import cosine_matrix, lexical_score


def test_cosine_and_index():
    v = np.array([[1.0, 0.0], [1.0, 0.0], [0.0, 1.0]])
    m = cosine_matrix(v)
    assert m[0, 1] > 0.99 and abs(m[0, 2]) < 1e-6
    items = [
        {"document_id": "a", "text": "first"},
        {"document_id": "b", "text": "second"},
        {"document_id": "c", "text": "third"},
    ]
    index = NumpyIndex(v, items)
    assert index.search([1, 0])[0][0] is items[0]
    assert index.search([1, 0], exclude_document_id="a")[0][0] is items[1]
    assert np.allclose(index.similarity_matrix(), m)
    assert lexical_score("shared community garden", "shared community garden") > 0.99


def test_lexical_signal_for_overlapping_paraphrase():
    score = lexical_score(
        "neighbors transformed vacant land into a shared garden",
        "neighbors transformed vacant land into community garden plots",
    )
    assert 0 < score < 1
