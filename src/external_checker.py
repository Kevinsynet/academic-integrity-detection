"""Read and validate local, reusable reference-corpus entries."""

import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)
REQUIRED_FIELDS = ("reference_id", "title", "source_name", "source_text")


def load_references(path):
    """Return valid references; report unavailable or malformed corpus data."""
    reference_path = Path(path)
    if not reference_path.exists():
        log.warning("Reference corpus is unavailable: %s", reference_path)
        return []
    try:
        data = json.loads(reference_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        log.warning("Could not read reference corpus %s: %s", reference_path, exc)
        return []

    entries = data.get("references") if isinstance(data, dict) else data
    if not isinstance(entries, list):
        log.warning(
            "Reference corpus %s must contain a list of references", reference_path
        )
        return []

    valid = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            log.warning("Skipping reference entry %d: expected an object", index)
            continue
        missing = [
            field
            for field in REQUIRED_FIELDS
            if not isinstance(entry.get(field), str) or not entry[field].strip()
        ]
        if missing:
            log.warning(
                "Skipping reference entry %d: missing or empty fields %s",
                index,
                ", ".join(missing),
            )
            continue
        source_url = entry.get("source_url")
        if source_url is not None and not isinstance(source_url, str):
            log.warning(
                "Skipping reference entry %d: source_url must be text or null", index
            )
            continue
        valid.append(entry)
    if not valid:
        log.warning("Reference corpus %s contains no valid entries", reference_path)
    return valid
