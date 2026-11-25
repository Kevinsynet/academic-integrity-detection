"""Write reviewer-facing individual and batch reports."""

import csv
import json
import os
from pathlib import Path


def _score_label(match):
    if match.get("vector_similarity_kind") == "semantic_embedding":
        return "MiniLM semantic cosine"
    return "TF-IDF vector cosine (lexical only)"


def write_report(report, outdir):
    p = Path(outdir)
    p.mkdir(parents=True, exist_ok=True)
    did = report["document_id"]
    (p / f"{did}.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
    original = report.get("original_submission")
    source_link = ""
    if original:
        relative = report.get("original_submission_link", original)
        source_link = f"\n\n**Original submission:** [{Path(original).name}]({relative})"
    lines = [
        f"# Integrity review: {did}", "",
        f"**Risk classification:** {report['total_integrity_risk']}{source_link}", "",
        "## Signal breakdown", "",
        f"- Peer similarity: {report['scores']['peer_similarity_percentage']:.1f}%",
        f"- External similarity: {report['scores']['external_similarity_percentage']:.1f}%",
        f"- AI heuristic indicator: {report['scores']['ai_generated_probability']:.1%}", "",
        "## Embedding and comparison", "",
        f"- Backend: {report['processing_metadata']['embedding_backend']}",
        f"- Score method: {report['processing_metadata'].get('score_method', 'unspecified')}",
        f"- Rule: {report['processing_metadata']['comparison_score']}",
        f"- Threshold: {report['processing_metadata']['threshold']}", "", "## Matches", "",
    ]
    risk_thresholds = report["processing_metadata"].get("risk_thresholds")
    if risk_thresholds:
        matches_index = lines.index("## Matches")
        lines[matches_index - 1:matches_index] = [
            "",
            f"- Risk bands: MEDIUM at {risk_thresholds['medium']}% coverage; "
            f"HIGH at {risk_thresholds['high']}% coverage",
            "",
        ]
    for key in ("peer_matches", "multimodal_matches", "external_matches"):
        lines += [f"### {key.replace('_', ' ').title()}"]
        for match in report[key][:10]:
            reference = match.get("reference", {})
            ref_label = ""
            if match.get("matched_submission_link"):
                ref_label = f"; source submission: [{Path(match['matched_submission']).name}]({match['matched_submission_link']})"
            if reference:
                title = reference.get("title") or reference.get("source_name") or "Local reference"
                ref_label = f"; reference: {title}"
                if reference.get("source_url"):
                    ref_label += f" ({reference['source_url']})"
            lines += [
                f"- **{match['matched_document']}** (combined {match['combined_similarity']:.3f}; "
                f"{_score_label(match)} {match['cosine_similarity']:.3f}; lexical cosine "
                f"{match['lexical_similarity']:.3f}; {match['query_location']} ↔ "
                f"{match['matched_location']}{ref_label})\n"
                f"  - Query: “{match['query_passage']}”\n"
                f"  - Source: “{match['matched_passage']}”\n"
                f"  - {match['explanation']}"
            ]
        if not report[key]:
            lines.append("- No significant matches detected.")
        lines.append("")
    lines += ["## AI analysis limitations", "", report["ai_analysis"].get("explanation", ""), "", "## Warnings", ""]
    lines += [f"- {warning}" for warning in report["warnings"]] or ["- None recorded."]
    (p / f"{did}.md").write_text("\n".join(lines))


def write_aggregate(reports, outdir, matrix, skipped_files=None):
    skipped_files = skipped_files or []
    failed = sum(report["extraction_status"] == "error" for report in reports)
    empty = sum(report["extraction_status"] == "empty" for report in reports)
    skipped_video = sum(report["extraction_status"] == "video_skipped" for report in reports)
    successful = len(reports) - failed - empty - skipped_video
    p = Path(outdir)
    summary = {
        "documents": len(reports), "risk_counts": {},
        "processing_counts": {"successful_with_text": successful, "empty_or_no_speech": empty,
                              "failed_extraction": failed, "skipped_video": skipped_video,
                              "skipped_unsupported": len(skipped_files)},
        "skipped_files": [str(x) for x in skipped_files], "reports": [],
    }
    for report in reports:
        risk = report["total_integrity_risk"]
        summary["risk_counts"][risk] = summary["risk_counts"].get(risk, 0) + 1
        summary["reports"].append({"document_id": report["document_id"], "risk": risk, "scores": report["scores"]})
    (p / "aggregate_summary.json").write_text(json.dumps(summary, indent=2))
    failure_label = "extraction failure" if failed == 1 else "extraction failures"
    status = (f"Processed {len(reports)} files: {successful} with text, {empty} empty/no-speech, "
              f"{failed} {failure_label}, {skipped_video} videos skipped, "
              f"{len(skipped_files)} unsupported files skipped.")
    (p / "aggregate_summary.md").write_text(
        "# Batch integrity summary\n\n" + status + "\n\n" +
        "\n".join(f"- {item['document_id']}: {item['risk']} "
                  f"(peer {item['scores']['peer_similarity_percentage']:.1f}%, "
                  f"external {item['scores']['external_similarity_percentage']:.1f}%)"
                  for item in summary["reports"]) + "\n\n## Skipped files\n\n" +
        "\n".join(f"- {item}" for item in skipped_files))
    with (p / "similarity_matrix.csv").open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["document_id"] + [item["document_id"] for item in reports])
        for index, report in enumerate(reports):
            writer.writerow([report["document_id"]] + matrix[index].tolist())
