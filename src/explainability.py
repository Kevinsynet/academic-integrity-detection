"""Reviewer-friendly source locations and explanations for candidate matches."""


def location(metadata):
    if "page" in metadata:
        return f"page {metadata['page']}"
    if "start" in metadata:
        return f"{metadata['start']:.1f}–{metadata.get('end', metadata['start']):.1f}s"
    if "paragraph" in metadata:
        return f"paragraph {metadata['paragraph']}"
    if "table" in metadata:
        return f"table {metadata['table']}, row {metadata.get('row', '?')}"
    return "location unavailable"


def make_match(query, source, score, lexical, category, combined=None, vector_kind="semantic_embedding"):
    combined = float(score) if combined is None else float(combined)
    score_label = "semantic embedding cosine" if vector_kind == "semantic_embedding" else "TF-IDF vector cosine"
    explanation = (
        f"The {score_label} is {score:.3f}, lexical cosine is {lexical:.3f}, and "
        f"the 0.8/0.2 combined score is {combined:.3f}; verify the displayed excerpts and locations."
    )
    return {
        "query_document": query["document_id"],
        "matched_document": source["document_id"],
        "query_passage": query["text"],
        "matched_passage": source["text"],
        "cosine_similarity": round(float(score), 4),
        "lexical_similarity": round(float(lexical), 4),
        "combined_similarity": round(combined, 4),
        "vector_similarity_kind": vector_kind,
        "query_location": location(query["metadata"]),
        "matched_location": location(source["metadata"]),
        "match_category": category,
        "explanation": explanation,
    }
