import json

from src.reporter import write_report


def _report():
    return {
        "document_id": "fallback_doc",
        "original_submission": "pdf/fallback_doc.pdf",
        "original_submission_link": "../input/pdf/fallback_doc.pdf",
        "filename": "fallback_doc.pdf",
        "total_integrity_risk": "LOW",
        "scores": {
            "peer_similarity_percentage": 0,
            "external_similarity_percentage": 0,
            "ai_generated_probability": 0,
        },
        "processing_metadata": {
            "embedding_backend": "tfidf_fallback",
            "score_method": "combined_tfidf_only",
            "comparison_score": "0.8 * TF-IDF + 0.2 * lexical",
            "threshold": 0.6,
            "risk_thresholds": {"medium": 10, "high": 25},
        },
        "peer_matches": [
            {
                "matched_document": "source",
                "combined_similarity": 0.7,
                "cosine_similarity": 0.72,
                "lexical_similarity": 0.62,
                "vector_similarity_kind": "tfidf_lexical",
                "query_location": "page 1",
                "matched_location": "page 2",
                "query_passage": "query words",
                "matched_passage": "source words",
                "explanation": "lexical only",
            }
        ],
        "multimodal_matches": [],
        "external_matches": [],
        "ai_analysis": {"explanation": "heuristic"},
        "warnings": [],
    }


def test_tfidf_report_never_calls_score_semantic(tmp_path):
    write_report(_report(), tmp_path)
    markdown = (tmp_path / "fallback_doc.md").read_text()
    assert "TF-IDF vector cosine (lexical only)" in markdown
    assert "semantic cosine" not in markdown
    assert "combined_tfidf_only" in markdown
    assert "\n\n## Matches\n\n" in markdown
    saved = json.loads((tmp_path / "fallback_doc.json").read_text())
    assert saved["original_submission"] == "pdf/fallback_doc.pdf"


def test_duplicate_filename_stems_get_distinct_reports_and_source_links(tmp_path):
    import pymupdf as fitz

    from src.config import Config
    from src.pipeline import run_pipeline

    input_dir = tmp_path / "input"
    (input_dir / "pdf").mkdir(parents=True)
    (input_dir / "docx").mkdir()
    out = tmp_path / "reports"
    for rel, text in (
        (
            "pdf/shared.pdf",
            "A coastal team measured tide pools during three seasonal surveys.",
        ),
        (
            "docx/shared.docx",
            "A mountain team mapped snow depth along several winter trails.",
        ),
    ):
        path = input_dir / rel
        if path.suffix == ".pdf":
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((50, 70), text)
            doc.save(path)
            doc.close()
        else:
            from docx import Document

            doc = Document()
            doc.add_paragraph(text)
            doc.save(path)
    reports, _ = run_pipeline(
        input_dir, out, Config(threshold=0.6), tmp_path / "no_refs", skip_video=True
    )
    assert len({item["document_id"] for item in reports}) == 2
    assert all(
        item["document_id"].endswith(tuple("0123456789abcdef")) for item in reports
    )
    for report in reports:
        saved = json.loads((out / f"{report['document_id']}.json").read_text())
        assert saved["original_submission"] in {"pdf/shared.pdf", "docx/shared.docx"}
        md = (out / f"{report['document_id']}.md").read_text()
        assert "Original submission:" in md
        assert "shared." in md


def test_external_reference_positive_evidence_and_negative_control(tmp_path):
    import pymupdf as fitz

    from src.config import Config
    from src.pipeline import run_pipeline

    input_dir = tmp_path / "input"
    input_dir.mkdir()
    refs = tmp_path / "refs"
    refs.mkdir()
    source = (
        "The archive team catalogued handwritten maps from the northern valley. Volunteers recorded "
        "each map's scale, paper condition, and publication date, then compared the records with "
        "the regional transport collection. This fictional reference passage documents a careful "
        "method for preserving local historical materials."
    )
    (refs / "references.json").write_text(
        json.dumps(
            {
                "references": [
                    {
                        "reference_id": "ref-norvale-test",
                        "title": "Synthetic map archive study",
                        "source_name": "Regression reference",
                        "source_text": source,
                        "source_url": None,
                    }
                ]
            }
        )
    )
    samples = {
        "reference_copy": source,
        "unrelated": "A marine biology group counted shellfish along a southern beach after winter storms. "
        "Researchers compared salinity and wave height at four observation sites.",
    }
    for name, text in samples.items():
        doc = fitz.open()
        page = doc.new_page()
        page.insert_textbox((50, 50, 540, 760), text, fontsize=11)
        doc.save(input_dir / f"{name}.pdf")
        doc.close()
    reports, _ = run_pipeline(
        input_dir, tmp_path / "reports", Config(threshold=0.6), refs, skip_video=True
    )
    by_id = {item["document_id"]: item for item in reports}
    matches = by_id["reference_copy"]["external_matches"]
    assert any(match["matched_document"] == "ref-norvale-test" for match in matches)
    match = next(
        match for match in matches if match["matched_document"] == "ref-norvale-test"
    )
    assert "handwritten maps" in match["matched_passage"]
    assert match["reference"]["title"] == "Synthetic map archive study"
    assert by_id["unrelated"]["external_matches"] == []
