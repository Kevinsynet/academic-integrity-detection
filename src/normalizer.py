"""Text cleanup and conservative corpus-frequency boilerplate filtering."""

import re

_TEMPLATE_MARKERS = (
    "synthetic case study",
    "fictional observations",
    "institutional prompt",
)
_ADMIN_MARKERS = (
    "all submissions",
    "review protocol",
    "reporting format",
    "administrative note",
    "submission guidelines",
    "assignment instructions",
    "this template",
    "shared template",
    "for this demonstration",
    "the following requirements",
    "please submit",
)


def normalize_text(text):
    """Normalize whitespace and soft hyphens without changing word meaning."""
    normalized = text.replace("\u00ad", "")
    normalized = re.sub(r"[\t\r\f]+", " ", normalized)
    normalized = re.sub(r"[ ]{2,}", " ", normalized)
    normalized = re.sub(r"\n[ \t]*\n(?:[ \t]*\n)+", "\n\n", normalized)
    return normalized.strip()


def remove_repeated_template_sentences(documents, fraction=0.5):
    """Remove frequent, recognizable template sentences while preserving analysis.

    Frequency alone is insufficient: a copied analytical finding remains useful
    evidence even if it appears in several submissions. Candidate sentences also
    need a recognizable template or administrative cue.
    """
    sentence_document_counts = {}
    marked_templates = set()

    for document in documents:
        seen_in_document = set()
        for segment in document.get("source_segments", []):
            sentences = re.split(r"(?<=[.!?])\s+", segment.get("text", ""))
            for sentence in sentences:
                key = " ".join(sentence.lower().split())
                is_marked = any(marker in key for marker in _TEMPLATE_MARKERS)
                is_administrative = any(marker in key for marker in _ADMIN_MARKERS)
                if key and (is_marked or (len(key.split()) >= 8 and is_administrative)):
                    seen_in_document.add(key)
                    if is_marked:
                        marked_templates.add(key)
        for key in seen_in_document:
            sentence_document_counts[key] = sentence_document_counts.get(key, 0) + 1

    document_count = max(1, len(documents))
    repeated = {
        key
        for key, count in sentence_document_counts.items()
        if count / document_count >= fraction
        and (count >= 3 or (key in marked_templates and count >= 2))
    }

    for document in documents:
        for segment in document.get("source_segments", []):
            sentences = re.split(r"(?<=[.!?])\s+", segment.get("text", ""))
            segment["text"] = " ".join(
                sentence
                for sentence in sentences
                if " ".join(sentence.lower().split()) not in repeated
            )
        document["extracted_text"] = " ".join(
            segment.get("text", "") for segment in document.get("source_segments", [])
        )
    return repeated
