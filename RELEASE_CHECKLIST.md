# Release readiness checklist

## Repository contents

- `src/`: 13 focused Python modules for extraction, transcription, normalization, chunking, embeddings, similarity, reference checking, orchestration, evidence, and reports.
- `run_integrity_check.py`: backward-compatible batch CLI.
- `scripts/`: synthetic development/hold-out dataset generators and the manifest-driven evaluator.
- `tests/`: 12 modules, 28 tests.
- `sample_submissions/`: 14 fictional samples (6 PDF, 5 DOCX, 3 MP4), a ground-truth manifest, spoken TTS clips, and degraded controls.
- `evaluation/holdout_submissions/`: separate 5-file synthetic hold-out plus manifest.
- `reference_data/`, `README.md`, `EVALUATION.md`, `CODE_AUDIT.md`, `INTERVIEW_PREPARATION.md`, `requirements.txt`, and an explicit no-license notice in the README and release notes. The inaccurate `LICENSE` file was removed.
- `reports/` and `evaluation/holdout_reports/` contain regenerated individual and aggregate reports plus similarity matrices. They are ignored by default to reduce accidental disclosure risk; this release explicitly stages the verified synthetic outputs because they are required deliverables. Never add reports from real submissions.

## Cleanup performed

Removed the stale 1.4 GB in-repository `.venv`, Python bytecode and `__pycache__` directories, `.pytest_cache`, and `.DS_Store` metadata. The environment's `pip` launcher referenced a different, missing workspace path; a clean environment outside the repository was used for verification. No source modules, tests, synthetic inputs, manifests, evaluation results, or generated reports were deleted.

The audit and interview-preparation documents were retained. The audit was explicitly requested in earlier project work; the interview-preparation document's purpose is not clear enough to delete without confirmation.

## Verification performed

A fresh Python 3.11 virtual environment was installed from `requirements.txt` outside the repository. `pip check` reported no broken requirements. FFmpeg and FFprobe were available as version 9.0.2. The real MiniLM model loaded; both spoken development MP4 files were transcribed by faster-whisper and produced timestamped cross-modal matches.

- `python -m compileall -q src scripts tests run_integrity_check.py` — passed.
- `python -m pytest -q` — **28 passed, 5 warnings** in 15.70 seconds. The warnings are PyMuPDF/SWIG deprecations.
- Development CLI — exit 0; 14 supported files, 1 corrupt-PDF extraction failure, 2 empty/no-speech cases, 1 unsupported manifest file skipped. Runtime output also included a Hugging Face unauthenticated-request/rate-limit notice, a CTranslate2 optional-MPS performance tip, and a PyTorch macOS redirection note; these did not prevent model loading or processing.
- Hold-out CLI — exit 0; 5 supported files, no extraction failures, 1 unsupported manifest file skipped. The spoken hold-out MP4 is 24.6 seconds after shortening its generated speech to the matched passage; timestamped Whisper matching was reverified.
- Development evaluation — 91 pairs; TP/FP/FN/TN = 11/0/0/80; precision/recall/F1 = 1.000/1.000/1.000.
- Hold-out evaluation — 10 pairs; TP/FP/FN/TN = 6/0/0/4; precision/recall/F1 = 1.000/1.000/1.000. The 0.60 threshold was not selected on hold-out examples.
- Scenario metrics and boilerplate controls are recorded in `EVALUATION.md`; these perfect scores are controlled synthetic regression results, not estimates of real-world accuracy.
- Verified 14 development and 5 hold-out individual JSON/Markdown reports, aggregate summaries, source/evidence links, and 15×15 / 6×6 similarity matrices. Both split evaluation JSON files identify `sentence-transformers/all-MiniLM-L6-v2` as the backend.
- Scanned source, documentation, and generated text reports for local absolute paths, obvious credential patterns, and personal identifiers; none were found. No model weights or large files are in the repository tree.
- Before release staging, `git status` showed all project files as untracked on `main`; no remote is configured and no commit exists. Release deliverables are staged for review; no commit or push has been made, and Git history has not been altered.

## Remaining risks before public release

- No license has been selected because project ownership and licensing rights could not be established. Public visibility does not grant reuse permission; add a license later only after confirming the rights holder and terms.
- The synthetic development and hold-out sets are very small and share fictional source material; perfect metrics do not demonstrate real-world accuracy. The AI-style score is uncalibrated, the local reference corpus is synthetic, and OCR is not implemented. See `EVALUATION.md` for other limitations and ambiguous cases.
- Generated reports are ignored by default. They contain synthetic examples at present and are reproducible, but inspect them before any deliberate force-add; never publish reports generated from real submissions.
- `CODE_AUDIT.md` and `INTERVIEW_PREPARATION.md` remain in the repository because their deletion was not clearly authorized.

## Suggested Git commands

After reviewing the current staged file list, provide the exact public GitHub repository URL. Once the URL is set and you approve commit and push, run the corresponding commit and push commands below. Do not use these commands before that confirmation.

```bash
git remote add origin <exact-public-repository-url>
git status --short
git diff --cached --check
git diff --cached --stat
git commit -m "Prepare integrity detection project for release"
git push -u origin main
```

The report directories are intentionally ignored by `.gitignore`, so this reviewed synthetic report set was added explicitly. Regenerate them with the README commands after installing dependencies. Do not stage report files generated from real submission text.
