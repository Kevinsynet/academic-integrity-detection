import json
import subprocess
from pathlib import Path


def test_development_dataset_manifest_matches_real_media_and_ground_truth():
    root = Path(__file__).resolve().parents[1]
    base = root / "sample_submissions"
    manifest = json.loads((base / "dataset_manifest.json").read_text())
    files = [path for path in base.rglob("*") if path.is_file() and path.suffix.lower() in {".pdf", ".docx", ".mp4"}]
    assert len(files) == len(manifest["submissions"]) == 14
    assert sum(path.suffix.lower() == ".pdf" for path in files) >= 5
    assert sum(path.suffix.lower() == ".docx" for path in files) >= 5
    assert 2 <= sum(path.suffix.lower() == ".mp4" for path in files) <= 3
    assert {path.stem for path in files} == {item["id"] for item in manifest["submissions"]}
    assert all((base / relative).is_file() for relative in manifest["known_degraded_files"])
    cross_modal = [item for item in manifest["expected_relationships"] if item["type"].startswith("cross-modal")]
    assert {item["a"] for item in cross_modal} | {item["b"] for item in cross_modal} >= {
        "garden_spoken", "original_river_spoken",
    }
    for video in sorted((base / "video").glob("*.mp4")):
        duration = float(subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
            text=True,
        ).strip())
        assert 10 <= duration <= 30
