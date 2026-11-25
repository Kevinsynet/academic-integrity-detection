"""Generate the fictional multimodal development dataset."""

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import pymupdf as fitz
from docx import Document

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "sample_submissions"
BOILERPLATE = (
    "This synthetic case study examines community resilience and responsible use of shared resources. "
    "The analysis uses fictional observations created for software testing."
)
GARDEN_SOURCE = (
    "The fictional town of Alderwick converted an unused lot into a neighborhood garden. Residents "
    "formed watering teams, tracked soil moisture each week, and compared harvests. Shared rules "
    "helped distribute work and gave apartment residents access to fresh food."
)
GARDEN_PARAPHRASE = (
    "In Alderwick, neighbors transformed vacant municipal land into a communal growing space. They "
    "rotated irrigation duties, recorded weekly moisture readings, and reviewed plot yields. A simple "
    "shared schedule spread the labor while extending produce access to people in flats."
)
COASTAL_SOURCE = (
    "A coastal village tested a library of repair tools. Membership records showed that weekend "
    "opening hours mattered more than the number of tools, because most residents worked weekdays. "
    "The committee therefore piloted evening lending and measured return rates."
)
RIVER_SOURCE = (
    "A fictional river monitoring group found that placing sampling kits near bus stops increased "
    "volunteer participation. The team compared weekly signups and found transport access mattered "
    "more than reminder frequency."
)
RIVER_SPOKEN = RIVER_SOURCE + (
    " They repeated observations across seasonal surveys and shared the results with the local "
    "watershed council."
)


def write_pdf(path, text):
    document = fitz.open()
    page = document.new_page()
    if text:
        page.insert_textbox((60, 60, 540, 760), text, fontsize=11)
    document.save(path)
    document.close()


def write_docx(path, text):
    document = Document()
    document.add_heading(path.stem, 0)
    document.add_paragraph(BOILERPLATE)
    document.add_paragraph(text)
    table = document.add_table(rows=1, cols=2)
    table.rows[0].cells[0].text = "Measure"
    table.rows[0].cells[1].text = "Observation"
    table.add_row().cells[0].text = "Trial"
    document.save(path)


def _tts_command(engine, wav_path, text):
    if engine == "say":
        return [engine, "-v", "Samantha", "-r", "160", "-o", str(wav_path), text]
    return [engine, "-v", "en-us", "-s", "155", "-w", str(wav_path), text]


def create_spoken_video(engine, temp_dir, filename, spoken_text):
    wav_path = temp_dir / f"{Path(filename).stem}.aiff"
    subprocess.run(_tts_command(engine, wav_path, spoken_text), check=True)
    if not wav_path.exists() or wav_path.stat().st_size < 10_000:
        raise RuntimeError(f"TTS did not produce usable speech for {filename}.")
    output = BASE / "video" / filename
    subprocess.run(
        [
            "ffmpeg",
            "-nostdin",
            "-v",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=black:s=320x240:r=10",
            "-i",
            str(wav_path),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-shortest",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            str(output),
        ],
        check=True,
    )
    duration = float(
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "csv=p=0",
                str(output),
            ],
            text=True,
        ).strip()
    )
    if not 10 <= duration <= 30:
        raise RuntimeError(
            f"{filename} duration {duration:.2f}s is outside 10–30 seconds."
        )


def build_manifest():
    submissions = [
        {"id": "garden_original", "kind": "original"},
        {"id": "garden_copy", "kind": "exact-copy", "related_to": "garden_original"},
        {
            "id": "coastal_paraphrase",
            "kind": "paraphrase",
            "related_to": "garden_original",
        },
        {
            "id": "garden_paraphrase",
            "kind": "paraphrase",
            "related_to": "garden_original",
        },
        {
            "id": "garden_spoken",
            "kind": "spoken-cross-modal-sample",
            "related_to": "garden_original",
        },
        {"id": "repair_original", "kind": "independent"},
        {"id": "repair_independent", "kind": "independent"},
        {"id": "island_original", "kind": "independent"},
        {"id": "original_river", "kind": "independent"},
        {
            "id": "original_river_spoken",
            "kind": "spoken-cross-modal-sample",
            "related_to": "original_river",
        },
        {"id": "llm_style_synthetic", "kind": "synthetic-style-experiment"},
        {"id": "silent_clip", "kind": "degraded-silent-video"},
        {"id": "empty_text", "kind": "degraded-empty-pdf"},
        {"id": "corrupted", "kind": "degraded-corrupt-pdf"},
    ]
    relationships = [
        {"a": "garden_original", "b": "garden_copy", "type": "exact-copy"},
        {
            "a": "garden_original",
            "b": "garden_spoken",
            "type": "cross-modal-exact-content",
        },
        {
            "a": "original_river",
            "b": "original_river_spoken",
            "type": "cross-modal-exact-content",
        },
        {"a": "garden_original", "b": "coastal_paraphrase", "type": "paraphrase"},
        {"a": "garden_original", "b": "garden_paraphrase", "type": "paraphrase"},
        {"a": "coastal_paraphrase", "b": "garden_paraphrase", "type": "exact-copy"},
        {"a": "garden_copy", "b": "coastal_paraphrase", "type": "paraphrase"},
        {"a": "garden_copy", "b": "garden_paraphrase", "type": "paraphrase"},
        {"a": "garden_copy", "b": "garden_spoken", "type": "cross-modal-exact-content"},
        {
            "a": "garden_spoken",
            "b": "coastal_paraphrase",
            "type": "cross-modal-paraphrase",
        },
        {
            "a": "garden_spoken",
            "b": "garden_paraphrase",
            "type": "cross-modal-paraphrase",
        },
    ]
    controls = [
        {"a": "garden_original", "b": "island_original"},
        {"a": "garden_original", "b": "repair_original"},
        {"a": "coastal_paraphrase", "b": "repair_original"},
        {"a": "original_river", "b": "island_original"},
        {"a": "garden_paraphrase", "b": "repair_independent"},
    ]
    return {
        "synthetic": True,
        "submissions": submissions,
        "expected_relationships": relationships,
        "boilerplate_control_pairs": controls,
        "known_degraded_files": [
            "pdf/corrupted.pdf",
            "pdf/empty_text.pdf",
            "video/silent_clip.mp4",
        ],
        "notes": (
            "All content is fictional. garden_spoken.mp4 speaks the garden_original passage; "
            "original_river_spoken.mp4 speaks the original_river passage with additional fictional "
            "context. Both are generated with local English TTS and validated at 10–30 seconds. "
            "silent_clip.mp4 contains silence."
        ),
    }


def main():
    for subdirectory in ("pdf", "docx", "video"):
        (BASE / subdirectory).mkdir(parents=True, exist_ok=True)

    write_pdf(BASE / "pdf/garden_original.pdf", BOILERPLATE + " " + GARDEN_SOURCE)
    write_pdf(BASE / "pdf/garden_copy.pdf", BOILERPLATE + " " + GARDEN_SOURCE)
    write_pdf(BASE / "pdf/repair_original.pdf", BOILERPLATE + " " + COASTAL_SOURCE)
    write_pdf(
        BASE / "pdf/coastal_paraphrase.pdf", BOILERPLATE + " " + GARDEN_PARAPHRASE
    )
    write_pdf(BASE / "pdf/empty_text.pdf", "")
    write_docx(BASE / "docx/garden_paraphrase.docx", GARDEN_PARAPHRASE)
    write_docx(
        BASE / "docx/repair_independent.docx",
        "A fictional watershed group installed rain gauges at school rooftops. Student volunteers "
        "compared storm totals with creek levels and discovered that one neighborhood drain "
        "consistently delayed runoff measurements by about two hours.",
    )
    write_docx(
        BASE / "docx/island_original.docx",
        "On a fictional island, residents compared two compost collection schedules. A morning pickup "
        "reduced missed bins in the southern district, while an afternoon route worked better near "
        "the market. The council tested both routes for six weeks before choosing a mixed schedule.",
    )
    write_docx(
        BASE / "docx/llm_style_synthetic.docx",
        "The initiative demonstrates a multifaceted and highly impactful approach. Furthermore, the "
        "coordinated framework enables stakeholders to leverage shared responsibility. Consequently, "
        "measurable outcomes may support broader community wellbeing. These findings underscore the "
        "importance of continued collaboration.",
    )
    write_docx(BASE / "docx/original_river.docx", RIVER_SOURCE)

    engines = ("say", "espeak-ng", "espeak")
    engine = next((candidate for candidate in engines if shutil.which(candidate)), None)
    if engine is None:
        raise RuntimeError(
            "Install macOS say, espeak-ng, or espeak to generate real speech samples."
        )
    with tempfile.TemporaryDirectory(prefix="integrity-tts-") as temp:
        temp_dir = Path(temp)
        create_spoken_video(engine, temp_dir, "garden_spoken.mp4", GARDEN_SOURCE)
        create_spoken_video(engine, temp_dir, "original_river_spoken.mp4", RIVER_SPOKEN)
        subprocess.run(
            [
                "ffmpeg",
                "-nostdin",
                "-v",
                "error",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "color=c=black:s=320x240:r=10",
                "-f",
                "lavfi",
                "-i",
                "anullsrc=r=16000:cl=mono",
                "-t",
                "12",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                str(BASE / "video/silent_clip.mp4"),
            ],
            check=True,
        )

    (BASE / "pdf/corrupted.pdf").write_bytes(b"%PDF-1.4\nnot a valid PDF body")
    manifest = build_manifest()
    (BASE / "dataset_manifest.json").write_text(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
