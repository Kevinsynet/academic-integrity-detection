"""Dense semantic embeddings with an explicit lexical-only fallback."""

import logging

import numpy as np

log = logging.getLogger(__name__)


class Embedder:
    """Load MiniLM first; use corpus-fitted TF-IDF only when it cannot load."""

    def __init__(
        self, device="cpu", model_name="sentence-transformers/all-MiniLM-L6-v2"
    ):
        self.model_name = model_name
        self.model = None
        self.vectorizer = None
        self.fallback = False
        self.failure_reason = None
        self.backend = model_name

        try:
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer(model_name, device=device)
            log.info("Loaded semantic embedding model %s on %s", model_name, device)
        except Exception as exc:  # noqa: BLE001 - any load failure must activate the documented fallback
            self.fallback = True
            self.backend = "scikit-learn TF-IDF (lexical-only fallback)"
            self.failure_reason = f"{type(exc).__name__}: {exc}"
            log.error(
                "Could not load semantic model %s (%s). Using TF-IDF lexical vectors; "
                "these scores are not semantic embeddings.",
                model_name,
                self.failure_reason,
            )

    def encode(self, texts, batch_size=32):
        texts = list(texts)
        if not texts:
            if self.model:
                dimension_fn = getattr(self.model, "get_embedding_dimension", None)
                if dimension_fn is None:
                    dimension_fn = self.model.get_sentence_embedding_dimension
                dimension = dimension_fn()
            else:
                dimension = 0
            return np.zeros((0, dimension), dtype=np.float32)

        if self.model is not None:
            vectors = self.model.encode(
                texts,
                batch_size=batch_size,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            return np.asarray(vectors, dtype=np.float32)

        from sklearn.feature_extraction.text import TfidfVectorizer

        if self.vectorizer is None:
            self.vectorizer = TfidfVectorizer(
                lowercase=True,
                ngram_range=(1, 2),
                sublinear_tf=True,
                token_pattern=r"(?u)\b\w+\b",
            )
            fit_texts = [
                text if any(char.isalnum() for char in text) else "emptytoken"
                for text in texts
            ]
            try:
                matrix = self.vectorizer.fit_transform(fit_texts)
            except ValueError as exc:
                if "empty vocabulary" not in str(exc).lower():
                    raise
                self.vectorizer = TfidfVectorizer(vocabulary={"emptytoken": 0})
                matrix = self.vectorizer.transform(["emptytoken"] * len(texts))
        else:
            safe_texts = [
                text if any(char.isalnum() for char in text) else "emptytoken"
                for text in texts
            ]
            matrix = self.vectorizer.transform(safe_texts)
        return matrix.toarray().astype(np.float32)
