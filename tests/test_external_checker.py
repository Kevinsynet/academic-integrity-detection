import json

from src.external_checker import load_references


def test_reference_loader_reports_missing_malformed_and_bad_entries(tmp_path, caplog):
    missing = tmp_path / "missing.json"
    assert load_references(missing) == []
    malformed = tmp_path / "malformed.json"
    malformed.write_text("{not json")
    assert load_references(malformed) == []
    path = tmp_path / "references.json"
    path.write_text(
        json.dumps(
            {
                "references": [
                    {
                        "reference_id": "valid",
                        "title": "Synthetic study",
                        "source_name": "Test",
                        "source_text": "Reusable source passage.",
                    },
                    {"reference_id": "invalid", "title": "Incomplete"},
                    "not an object",
                ]
            }
        )
    )
    references = load_references(path)
    assert [item["reference_id"] for item in references] == ["valid"]
    assert "Skipping reference entry" in caplog.text


def test_reference_loader_requires_reference_list(tmp_path):
    path = tmp_path / "bad_shape.json"
    path.write_text(json.dumps({"items": []}))
    assert load_references(path) == []
