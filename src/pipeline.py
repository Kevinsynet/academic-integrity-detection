"""Batch orchestration for extraction, embeddings, comparison, and reports."""

import hashlib
import logging
import os
import re
from collections import Counter
from pathlib import Path

import numpy as np

from .ai_detector import analyze_ai
from .chunker import chunk_document
from .config import Config
from .embeddings import Embedder
from .explainability import make_match
from .external_checker import load_references
from .extractors import extract_document
from .indexer import NumpyIndex
from .normalizer import remove_repeated_template_sentences
from .reporter import write_aggregate, write_report
from .similarity import lexical_score

log = logging.getLogger(__name__)
SUPPORTED = {".pdf", ".docx", ".mp4"}


def discover(input_dir):
    return sorted(
        path
        for path in Path(input_dir).rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED
    )


def discover_skipped(input_dir):
    return sorted(
        path
        for path in Path(input_dir).rglob("*")
        if path.is_file() and path.suffix.lower() not in SUPPORTED
    )


def _combined_score(cosine, lexical):
    """Keep dense semantic cosine primary; use lexical overlap as supporting evidence."""
    return 0.8 * float(cosine) + 0.2 * float(lexical)


def _deduplicate(matches):
    selected = {}
    for match in matches:
        key = (match["matched_document"], match["query_passage"][:120])
        old = selected.get(key)
        if old is None or match["combined_similarity"] > old["combined_similarity"]:
            selected[key] = match
    return sorted(
        selected.values(), key=lambda item: item["combined_similarity"], reverse=True
    )


def run_pipeline(
    input_dir,
    output_dir,
    config=None,
    reference_dir=None,
    skip_video=False,
    skipped_files=None,
):
    config = config or Config()
    paths = discover(input_dir)
    stem_counts = Counter(path.stem.casefold() for path in paths)

    def document_id(path):
        if stem_counts[path.stem.casefold()] == 1:
            return path.stem
        relative = path.relative_to(Path(input_dir)).with_suffix("")
        safe = re.sub(r"[^A-Za-z0-9_-]+", "_", relative.as_posix()).strip("_")
        digest = hashlib.sha256(relative.as_posix().encode("utf-8")).hexdigest()[:8]
        return f"{safe}__{digest}"

    docs = []
    for index, path in enumerate(paths, 1):
        print(f"[{index}/{len(paths)}] Extracting {path.name}")
        doc = extract_document(path, transcribe=not skip_video, device=config.device)
        doc["document_id"] = document_id(path)
        doc["original_submission"] = path.relative_to(Path(input_dir)).as_posix()
        doc["original_submission_link"] = os.path.relpath(
            path.resolve(), Path(output_dir).resolve()
        )
        docs.append(doc)

    remove_repeated_template_sentences(docs, config.boilerplate_fraction)
    chunks = [chunk_document(doc, config.chunk_size, config.overlap) for doc in docs]
    flat_chunks = [chunk for group in chunks for chunk in group]

    embedder = Embedder(config.device)
    vectors = embedder.encode(
        [chunk["text"] for chunk in flat_chunks], config.batch_size
    )
    vector_index = NumpyIndex(vectors, flat_chunks)
    similarity = vector_index.similarity_matrix()

    refs_path = (
        Path(reference_dir or Path(input_dir).parent / "reference_data")
        / "references.json"
    )
    ref_chunks = []
    for ref in load_references(refs_path):
        words = ref.get("source_text", "").split()
        for start in range(0, len(words), config.chunk_size):
            passage = " ".join(words[start : start + config.chunk_size])
            if passage.strip():
                ref_chunks.append(
                    {
                        "document_id": ref.get("reference_id", "reference"),
                        "text": passage,
                        "metadata": {
                            "title": ref.get("title", ""),
                            "source_name": ref.get("source_name", ""),
                            "source_url": ref.get("source_url"),
                        },
                    }
                )
    ref_vectors = embedder.encode(
        [item["text"] for item in ref_chunks], config.batch_size
    )

    doc_matrix = np.eye(len(docs), dtype=float)
    offsets = []
    offset = 0
    for group in chunks:
        offsets.append(offset)
        offset += len(group)

    reports = []
    for doc_index, doc in enumerate(docs):
        peer_matches = []
        external_matches = []
        eligible = [
            chunk for chunk in chunks[doc_index] if len(chunk["text"].split()) >= 12
        ]

        for query_index, query in enumerate(chunks[doc_index]):
            if len(query["text"].split()) < 12:
                continue
            query_vector_index = offsets[doc_index] + query_index

            for source_index, source_group in enumerate(chunks):
                if source_index == doc_index:
                    continue
                for source_chunk_index, source in enumerate(source_group):
                    if len(source["text"].split()) < 12:
                        continue
                    source_vector_index = offsets[source_index] + source_chunk_index
                    cosine = float(similarity[query_vector_index, source_vector_index])
                    lexical = lexical_score(query["text"], source["text"])
                    combined = _combined_score(cosine, lexical)
                    if combined < config.threshold:
                        continue

                    is_cross_modal = "mp4" in (
                        doc["file_type"],
                        docs[source_index]["file_type"],
                    )
                    category = (
                        "cross-modal"
                        if is_cross_modal
                        else "exact-copy"
                        if lexical >= 0.97
                        else "semantic"
                        if not embedder.fallback
                        else "lexical-fallback"
                    )
                    vector_kind = (
                        "tfidf_lexical" if embedder.fallback else "semantic_embedding"
                    )
                    match = make_match(
                        query, source, cosine, lexical, category, combined, vector_kind
                    )
                    match["matched_document"] = docs[source_index]["document_id"]
                    match["matched_submission"] = docs[source_index][
                        "original_submission"
                    ]
                    match["matched_submission_link"] = docs[source_index][
                        "original_submission_link"
                    ]
                    match["combined_similarity"] = round(combined, 4)
                    match["decision_threshold"] = config.threshold
                    peer_matches.append(match)
                    doc_matrix[doc_index, source_index] = max(
                        doc_matrix[doc_index, source_index], combined
                    )

            for ref_index, ref in enumerate(ref_chunks):
                if len(ref["text"].split()) < 12 or ref_index >= len(ref_vectors):
                    continue
                cosine = float(vectors[query_vector_index] @ ref_vectors[ref_index])
                lexical = lexical_score(query["text"], ref["text"])
                combined = _combined_score(cosine, lexical)
                if combined < config.threshold:
                    continue
                vector_kind = (
                    "tfidf_lexical" if embedder.fallback else "semantic_embedding"
                )
                match = make_match(
                    query,
                    ref,
                    cosine,
                    lexical,
                    "external-reference",
                    combined,
                    vector_kind,
                )
                match["matched_document"] = ref["document_id"]
                match["reference"] = ref.get("metadata", {})
                match["combined_similarity"] = round(combined, 4)
                match["decision_threshold"] = config.threshold
                external_matches.append(match)

        peer_matches = _deduplicate(peer_matches)
        external_matches = _deduplicate(external_matches)
        peer_covered = {match["query_passage"] for match in peer_matches}
        external_covered = {match["query_passage"] for match in external_matches}
        peer_pct = 100 * len(peer_covered) / max(1, len(eligible))
        external_pct = 100 * len(external_covered) / max(1, len(eligible))
        ai_analysis = analyze_ai(doc["extracted_text"])
        risk = (
            "HIGH"
            if peer_pct >= config.risk_high or external_pct >= config.risk_high
            else "MEDIUM"
            if peer_pct >= config.risk_medium or external_pct >= config.risk_medium
            else "LOW"
        )

        report = {
            "document_id": doc["document_id"],
            "filename": doc["filename"],
            "original_submission": doc["original_submission"],
            "original_submission_link": doc["original_submission_link"],
            "extraction_status": doc["extraction_status"],
            "total_integrity_risk": risk,
            "scores": {
                "peer_similarity_percentage": round(min(100, peer_pct), 2),
                "external_similarity_percentage": round(min(100, external_pct), 2),
                "ai_generated_probability": ai_analysis["ai_generated_probability"],
            },
            "peer_matches": peer_matches,
            "multimodal_matches": [
                match
                for match in peer_matches
                if match["match_category"] == "cross-modal"
            ],
            "external_matches": external_matches,
            "ai_analysis": ai_analysis,
            "explanations": [
                match["explanation"]
                for match in peer_matches[:5] + external_matches[:5]
            ],
            "warnings": doc["warnings"],
            "processing_metadata": {
                "chunk_count": len(chunks[doc_index]),
                "embedding_backend": embedder.backend,
                "score_method": "combined_tfidf_only"
                if embedder.fallback
                else "combined_minilm_tfidf",
                "embedding_model_error": embedder.failure_reason,
                "comparison_score": (
                    "0.8 * TF-IDF vector cosine + 0.2 * pairwise TF-IDF cosine (lexical-only)"
                    if embedder.fallback
                    else "0.8 * MiniLM semantic cosine + 0.2 * TF-IDF lexical cosine"
                ),
                "threshold": config.threshold,
                "risk_thresholds": {
                    "medium": config.risk_medium,
                    "high": config.risk_high,
                },
                "transcription_status": doc.get("metadata", {}).get(
                    "transcription_status"
                ),
            },
        }
        write_report(report, output_dir)
        reports.append(report)

    write_aggregate(reports, output_dir, doc_matrix, skipped_files=skipped_files or [])
    return reports, doc_matrix
