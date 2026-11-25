"""Robust PDF, DOCX, and MP4 extraction with explicit modality status."""

import logging
import math
import shutil
import struct
import subprocess
import tempfile
import wave
from pathlib import Path

log = logging.getLogger(__name__)
_WHISPER_MODELS = {}


def _whisper_model(name, device):
    key = (name, device)
    if key not in _WHISPER_MODELS:
        from faster_whisper import WhisperModel

        compute_type = "int8" if device == "cpu" else "float16"
        _WHISPER_MODELS[key] = WhisperModel(
            name, device=device, compute_type=compute_type
        )
    return _WHISPER_MODELS[key]


def extract_document(path, transcribe=True, whisper_model="tiny", device="cpu"):
    path = Path(path)
    extension = path.suffix.lower()
    segments = []
    warnings = []
    text = ""
    metadata = {}
    status = "error"

    try:
        if extension == ".pdf":
            import pymupdf

            with pymupdf.open(path) as pdf:
                for page_number, page in enumerate(pdf, start=1):
                    page_text = page.get_text("text").strip()
                    if page_text:
                        segments.append({"text": page_text, "page": page_number})
            text = "\n\n".join(segment["text"] for segment in segments)
            if not text:
                warnings.append(
                    "No extractable text; scanned image PDFs require a separately configured OCR step."
                )
            status = "ok" if text else "empty"

        elif extension == ".docx":
            from docx import Document

            document = Document(path)
            paragraph_number = 0
            for paragraph in document.paragraphs:
                if paragraph.text.strip():
                    paragraph_number += 1
                    segments.append(
                        {"text": paragraph.text.strip(), "paragraph": paragraph_number}
                    )
            for table_number, table in enumerate(document.tables, start=1):
                for row_number, row in enumerate(table.rows, start=1):
                    row_text = " | ".join(
                        cell.text.strip() for cell in row.cells if cell.text.strip()
                    )
                    if row_text:
                        segments.append(
                            {
                                "text": row_text,
                                "table": table_number,
                                "row": row_number,
                            }
                        )
            text = "\n".join(segment["text"] for segment in segments)
            status = "ok" if text.strip() else "empty"

        elif extension == ".mp4":
            if not transcribe:
                metadata["transcription_status"] = "skipped_by_option"
                return _result(
                    path,
                    "video_skipped",
                    [],
                    "",
                    ["Video processing disabled by --skip_video"],
                    metadata,
                )
            if not shutil.which("ffmpeg"):
                raise RuntimeError("FFmpeg executable was not found on PATH")

            with tempfile.TemporaryDirectory(prefix="integrity-audio-") as temp_dir:
                wav_path = Path(temp_dir) / "audio.wav"
                command = [
                    "ffmpeg",
                    "-nostdin",
                    "-v",
                    "error",
                    "-y",
                    "-i",
                    str(path),
                    "-vn",
                    "-ac",
                    "1",
                    "-ar",
                    "16000",
                    "-c:a",
                    "pcm_s16le",
                    "-f",
                    "wav",
                    str(wav_path),
                ]
                process = subprocess.run(
                    command, capture_output=True, text=True, check=False
                )
                if process.returncode != 0:
                    message = process.stderr.strip()[-700:] or "no audio stream found"
                    raise RuntimeError(f"FFmpeg audio extraction failed: {message}")
                if not wav_path.exists() or wav_path.stat().st_size < 1000:
                    metadata["transcription_status"] = "silent_or_too_short"
                    warnings.append(
                        "Audio stream is silent or too short to transcribe."
                    )
                    status = "empty"
                elif _is_silent(wav_path):
                    metadata["transcription_status"] = "silent"
                    warnings.append("Audio stream is silent; Whisper was not invoked.")
                    status = "empty"
                else:
                    model = _whisper_model(whisper_model, device)
                    iterator, info = model.transcribe(str(wav_path), vad_filter=True)
                    for segment in iterator:
                        spoken_text = segment.text.strip()
                        if spoken_text:
                            segments.append(
                                {
                                    "text": spoken_text,
                                    "start": float(segment.start),
                                    "end": float(segment.end),
                                }
                            )
                    text = " ".join(segment["text"] for segment in segments)
                    metadata.update(
                        {
                            "transcription_status": "transcribed"
                            if segments
                            else "no_speech",
                            "transcription_model": whisper_model,
                            "language": getattr(info, "language", None),
                            "language_probability": getattr(
                                info, "language_probability", None
                            ),
                        }
                    )
                    if segments:
                        status = "ok"
                    else:
                        status = "empty"
                        warnings.append(
                            "Whisper processed the audio but returned no speech segments."
                        )

        else:
            raise ValueError(f"Unsupported file extension: {extension or '<none>'}")

    except Exception as exc:  # noqa: BLE001 - isolate every per-file extraction failure
        status = "error"
        if extension == ".mp4":
            metadata["transcription_status"] = "error"
        warnings.append(f"Extraction failed: {type(exc).__name__}: {exc}")
        log.warning("%s: %s", path, warnings[-1])

    return _result(path, status, segments, text, warnings, metadata)


def _result(path, status, segments, text, warnings, metadata=None):
    return {
        "document_id": path.stem,
        "filename": path.name,
        "file_type": path.suffix.lower().lstrip("."),
        "extracted_text": text,
        "extraction_status": status,
        "metadata": metadata or {},
        "source_segments": segments,
        "warnings": warnings,
    }


def _is_silent(path):
    try:
        with wave.open(str(path), "rb") as audio:
            frame_count = audio.getnframes()
            if frame_count == 0:
                return True
            raw = audio.readframes(frame_count)
        sample_count = len(raw) // 2
        samples = struct.unpack("<" + "h" * sample_count, raw[: sample_count * 2])
        sampled = samples[:: max(1, len(samples) // 20000)]
        rms = math.sqrt(
            sum(sample * sample for sample in sampled) / max(1, len(sampled))
        )
        return rms < 40
    except (OSError, EOFError, wave.Error, struct.error):
        return False
