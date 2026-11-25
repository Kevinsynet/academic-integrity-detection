# GitHub release notes

## Repository

- **Name:** `academic-integrity-detection`
- **Description:** A Python-based multimodal academic integrity detection system that analyses PDF, DOCX and MP4 submissions using semantic embeddings, speech transcription and explainable similarity reports.
- **Suggested topics:** `python`, `machine-learning`, `nlp`, `semantic-similarity`, `sentence-transformers`, `whisper`, `academic-integrity`, `multimodal-ai`

## Project summary

This local screening prototype extracts document text and transcribes spoken audio, compares evidence across submissions and a supplied local reference corpus, and generates reviewer-oriented reports. Similarity signals flag passages for human review; they do not establish misconduct or authorship.

## Technical highlights

- PyMuPDF extracts PDF page text; python-docx reads DOCX paragraphs and table rows.
- FFmpeg extracts MP4 audio and faster-whisper transcribes speech into timestamped segments. The supplied synthetic dataset includes spoken English clips and a silent control.
- Text is normalized and split into overlapping, location-preserving chunks.
- Sentence Transformers `sentence-transformers/all-MiniLM-L6-v2` creates normalized dense embeddings. NumPy performs exact in-memory cosine comparisons; pairwise TF-IDF cosine contributes to the combined score. If MiniLM cannot load, the fallback is explicitly labeled TF-IDF and is lexical-only.
- Peer, local-reference, and uncalibrated AI-style heuristic signals are reported separately. Reports include source excerpts, filenames, pages or timestamps, and scoring details.
- The batch CLI produces individual JSON and Markdown reports, aggregate summaries, and a similarity matrix. `scripts/evaluate.py` measures manifest-defined development and hold-out relationships.

## Installation and run

Install FFmpeg first (`brew install ffmpeg` on macOS or `sudo apt install ffmpeg` on Debian/Ubuntu). From the repository root, create an environment, install dependencies, and run the sample batch:

```bash
python3.11 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt && .venv/bin/python run_integrity_check.py --input_dir ./sample_submissions --output_dir ./reports --reference_dir ./reference_data
```

MiniLM and Whisper model weights download on first use and are cached outside the repository. The `tiny` Whisper model is used by default. Generated reports can contain extracted submission text; review them before sharing. For this fictional sample dataset they can be regenerated with the commands in `README.md`.

## Evaluation summary

The current synthetic development run has 14 submissions and 91 candidate pairs: TP/FP/FN/TN **11/0/0/80**, precision/recall/F1 **1.000/1.000/1.000**. The separate synthetic hold-out has 5 submissions and 10 pairs: **6/0/0/4**, precision/recall/F1 **1.000/1.000/1.000**, at the unchanged 0.60 threshold. These are small controlled regression results, not estimates of real-world accuracy. See `EVALUATION.md` for scenario metrics, controls, and methodology.

## License status

No license has been selected because the rights holder and licensing conditions have not been established. The inaccurate MIT license file was removed; no open-source reuse permission is claimed.

## Limitations

The datasets and local reference material are fictional and small; related examples share source passages. The threshold was informed by development data, while the hold-out was not used for threshold selection. Scanned PDF OCR is not implemented, the AI-style score is an uncalibrated heuristic, and the reference checker does not search the web. ASR can misrecognize words. Matching is exact and in-memory, with quadratic all-pairs costs, and the prototype has not been hardened for untrusted production workloads. Reviewers must inspect source passages and original media.
