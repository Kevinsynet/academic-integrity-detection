"""Create a separate fictional hold-out set; threshold remains fixed at 0.60."""

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import pymupdf as fitz
from docx import Document

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "evaluation" / "holdout_submissions"
BOILER = ("All submissions use the same review protocol and shared reporting format for this "
          "demonstration project; this standard administrative note contains no findings.")
SOURCE = ("The fictional city of Norvale installed reflective roof panels at three public libraries. "
          "Over one summer, researchers measured indoor temperatures every afternoon and compared "
          "the readings with nearby buildings without panels. The libraries stayed cooler during "
          "heat waves, while shaded reading rooms remained open to residents who lacked air conditioning.")
PARAPHRASE = ("Three Norvale libraries received bright roof coatings in a made-up city experiment. "
              "Investigators recorded room heat each afternoon through the summer and used "
              "neighboring untreated buildings for comparison. During hot spells, the treated "
              "libraries had lower temperatures, and their shaded spaces offered a refuge for people "
              "whose homes had no cooling system.")
UNRELATED = ("A fictional marine laboratory compared two methods for counting plankton in coastal "
             "water samples. Technicians used microscope slides for one group and automated image "
             "analysis for another. Counts differed most after storms, when suspended sediment "
             "obscured small organisms. The team recommended collecting duplicate samples on calm days.")


def make_pdf(path, body):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_textbox((55, 55, 540, 760), f"{BOILER}\n\n{body}", fontsize=11)
    doc.save(path)
    doc.close()


def make_docx(path, body):
    doc = Document()
    doc.add_paragraph(BOILER)
    doc.add_paragraph(body)
    doc.save(path)


def main():
    for folder in ("pdf", "docx", "video"):
        (BASE / folder).mkdir(parents=True, exist_ok=True)
    make_pdf(BASE / "pdf" / "holdout_original.pdf", SOURCE)
    make_pdf(BASE / "pdf" / "holdout_exact_copy.pdf", SOURCE)
    make_docx(BASE / "docx" / "holdout_paraphrase.docx", PARAPHRASE)
    make_pdf(BASE / "pdf" / "holdout_unrelated.pdf", UNRELATED)

    spoken = SOURCE
    with tempfile.TemporaryDirectory() as temp:
        wav = Path(temp) / "holdout_speech.aiff"
        if shutil.which("say"):
            subprocess.run(["say", "-v", "Samantha", "-r", "170", "-o", str(wav), spoken], check=True)
        elif shutil.which("espeak-ng"):
            subprocess.run(["espeak-ng", "-v", "en-us", "-s", "165", "-w", str(wav), spoken], check=True)
        elif shutil.which("espeak"):
            subprocess.run(["espeak", "-v", "en-us", "-s", "165", "-w", str(wav), spoken], check=True)
        else:
            raise RuntimeError("A local TTS engine (say, espeak-ng, or espeak) is required for hold-out speech.")
        if not wav.exists() or wav.stat().st_size < 10000:
            raise RuntimeError("TTS did not produce usable speech audio.")
        output = BASE / "video" / "holdout_spoken.mp4"
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "lavfi", "-i",
                        "color=c=black:s=320x240:r=10", "-i", str(wav), "-map", "0:v:0", "-map", "1:a:0",
                        "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(output)], check=True)

    manifest = {
        "synthetic": True,
        "split": "holdout",
        "threshold_frozen_before_holdout_scoring": 0.60,
        "submissions": [
            {"id": "holdout_original"}, {"id": "holdout_exact_copy"},
            {"id": "holdout_paraphrase"}, {"id": "holdout_unrelated"}, {"id": "holdout_spoken"},
        ],
        "expected_relationships": [
            {"a": "holdout_original", "b": "holdout_exact_copy", "type": "exact-copy"},
            {"a": "holdout_original", "b": "holdout_paraphrase", "type": "paraphrase"},
            {"a": "holdout_exact_copy", "b": "holdout_paraphrase", "type": "paraphrase"},
            {"a": "holdout_original", "b": "holdout_spoken", "type": "cross-modal-exact-content"},
            {"a": "holdout_exact_copy", "b": "holdout_spoken", "type": "cross-modal-exact-content"},
            {"a": "holdout_paraphrase", "b": "holdout_spoken", "type": "cross-modal-paraphrase"},
        ],
        "boilerplate_control_pairs": [
            {"a": "holdout_original", "b": "holdout_unrelated"},
            {"a": "holdout_exact_copy", "b": "holdout_unrelated"},
            {"a": "holdout_paraphrase", "b": "holdout_unrelated"},
        ],
        "notes": "Fictional, independently authored hold-out content with exact-copy, paraphrase, speech, unrelated and shared administrative boilerplate cases. The 0.60 threshold is fixed from development configuration and was not selected using these examples.",
    }
    (BASE / "dataset_manifest.json").write_text(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
