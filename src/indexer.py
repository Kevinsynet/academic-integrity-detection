"""Exact, in-memory NumPy vector index for the small-batch prototype."""

import numpy as np


def normalize_rows(values):
    vectors = np.asarray(values, dtype=np.float32)
    if vectors.size == 0:
        return vectors.reshape(0, vectors.shape[-1] if vectors.ndim else 0)
    if vectors.ndim != 2:
        raise ValueError("Vector index expects a two-dimensional array.")
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / np.maximum(norms, 1e-12)


class NumpyIndex:
    """Exact cosine index; results map back to supplied chunk items."""

    def __init__(self, vectors, items):
        self.vectors = normalize_rows(vectors)
        self.items = list(items)
        if len(self.items) != len(self.vectors):
            raise ValueError("Each indexed vector must have one corresponding item.")

    def similarity_matrix(self):
        return self.vectors @ self.vectors.T

    def search(self, query, k=10, exclude_document_id=None):
        if k <= 0:
            return []
        query_vector = normalize_rows(np.asarray(query, dtype=np.float32).reshape(1, -1))[0]
        if query_vector.shape[0] != self.vectors.shape[1]:
            raise ValueError("Query vector dimension does not match the index.")
        scores = self.vectors @ query_vector
        ranked = np.argsort(-scores, kind="stable")
        results = []
        for index in ranked:
            item = self.items[int(index)]
            if exclude_document_id and item.get("document_id") == exclude_document_id:
                continue
            results.append((item, float(scores[index])))
            if len(results) >= max(0, k):
                break
        return results
