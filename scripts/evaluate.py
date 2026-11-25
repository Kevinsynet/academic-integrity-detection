"""Compute reproducible pair metrics from a manifest and a completed pipeline run."""

import argparse
import itertools
import json
from pathlib import Path
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score

ROOT = Path(__file__).resolve().parents[1]
CATEGORY_MAP = {
    "exact-copy": "exact-copy", "paraphrase": "paraphrase",
    "cross-modal-exact-content": "cross-modal", "cross-modal-paraphrase": "cross-modal",
}


def metrics(actual, predicted, universe):
    ordered_pairs = sorted(universe)
    actual_labels = [int(pair in actual) for pair in ordered_pairs]
    predicted_labels = [int(pair in predicted) for pair in ordered_pairs]
    # Label order [1, 0] yields [[TP, FN], [FP, TN]].
    matrix = confusion_matrix(actual_labels, predicted_labels, labels=[1, 0])
    tp, fn = int(matrix[0, 0]), int(matrix[0, 1])
    fp, tn = int(matrix[1, 0]), int(matrix[1, 1])
    return {
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision": float(precision_score(actual_labels, predicted_labels, zero_division=0)),
        "recall": float(recall_score(actual_labels, predicted_labels, zero_division=0)),
        "f1": float(f1_score(actual_labels, predicted_labels, zero_division=0)),
    }


def evaluate(reports_dir, manifest_path):
    manifest = json.loads(Path(manifest_path).read_text())
    reports = []
    for path in Path(reports_dir).glob("*.json"):
        try:
            report = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if report.get("document_id"):
            reports.append(report)
    ids = sorted(report["document_id"] for report in reports)
    expected_ids = sorted(item["id"] for item in manifest["submissions"])
    if ids != expected_ids:
        raise ValueError(f"Report IDs do not match manifest. Missing={sorted(set(expected_ids)-set(ids))}; "
                         f"extra={sorted(set(ids)-set(expected_ids))}")
    expected_by_pair = {}
    for rel in manifest["expected_relationships"]:
        if rel.get("evaluable", True):
            expected_by_pair[tuple(sorted((rel["a"], rel["b"]))) ] = CATEGORY_MAP[rel["type"]]
    predicted_score = {}
    for report in reports:
        for match in report["peer_matches"]:
            pair = tuple(sorted((report["document_id"], match["matched_document"])))
            if pair[0] == pair[1]:
                continue
            category = match["match_category"]
            if category == "semantic":
                category = "paraphrase"
            candidate = (match["combined_similarity"], category)
            if pair not in predicted_score or candidate[0] > predicted_score[pair][0]:
                predicted_score[pair] = candidate
    predicted_by_pair = {pair: value[1] for pair, value in predicted_score.items()}
    universe = set(itertools.combinations(ids, 2))
    expected = set(expected_by_pair)
    predicted = set(predicted_by_pair)
    scenario = {}
    for category in ("exact-copy", "paraphrase", "cross-modal"):
        actual = {pair for pair, label in expected_by_pair.items() if label == category}
        found = {pair for pair, label in predicted_by_pair.items() if label == category}
        scenario[category] = metrics(actual, found, universe)
    controls = {tuple(sorted((item["a"], item["b"])))
                for item in manifest.get("boilerplate_control_pairs", [])}
    false_controls = controls & predicted
    result = {
        "dataset_split": manifest.get("split", "development"),
        "synthetic": manifest.get("synthetic", False),
        "threshold": reports[0]["processing_metadata"]["threshold"] if reports else None,
        "embedding_backend": reports[0]["processing_metadata"]["embedding_backend"] if reports else None,
        "documents": len(ids), "evaluated_pairs": len(universe),
        "expected_positive_pairs": len(expected), "predicted_positive_pairs": len(predicted),
        **metrics(expected, predicted, universe),
        "confusion_matrix_actual_rows_predicted_columns": [
            [len(expected & predicted), len(expected - predicted)],
            [len(predicted - expected), len(universe - expected - predicted)],
        ],
        "scenario_metrics": scenario,
        "boilerplate_controls": {
            "control_pairs": len(controls), "false_positive_pairs": len(false_controls),
            "specificity_on_controls": (len(controls) - len(false_controls)) / len(controls) if controls else None,
            "false_positive_pair_ids": [list(pair) for pair in sorted(false_controls)],
        },
        "excluded_non_evaluable": [item for item in manifest["expected_relationships"]
                                   if not item.get("evaluable", True)],
    }
    return result


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--reports_dir", default=str(ROOT / "reports"))
    parser.add_argument("--manifest", default=str(ROOT / "sample_submissions/dataset_manifest.json"))
    parser.add_argument("--output", default=None)
    args = parser.parse_args(argv)
    result = evaluate(args.reports_dir, args.manifest)
    output = Path(args.output) if args.output else Path(args.reports_dir) / "evaluation_metrics.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
