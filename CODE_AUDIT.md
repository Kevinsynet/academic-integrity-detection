# Complete Technical Audit — integrity-detection

**Audit date:** 25 November 2026

**Scope:** Read-only review of the existing source, tests, scripts, sample inputs, reports, configuration, and documentation. The only project writes in this audit are this file and `INTERVIEW_PREPARATION.md`; the requested CLI/evaluation run regenerated the existing report outputs.

## Executive verdict

This is a working local screening prototype. In the environment available for this audit, it successfully loaded MiniLM, transcribed the spoken MP4 with faster-whisper, made cross-modal text-to-transcript matches, isolated malformed/empty inputs, and wrote reports. I independently reproduced the checked-in evaluator’s pair-level metrics from the manifest and individual reports.

It is **not ready to present as a reliable academic-integrity detector**. The observed 1.00 precision/recall/F1 is from a small, deliberately constructed synthetic set, and the threshold was selected on that same set. The system has no independent validation. External-reference matching has no positive regression test and produced no external matches in this run. There are also report-identity, fallback-label, repository-hygiene, and documentation defects to fix before a polished public release.

## What I ran and observed

Environment: project-local Python 3.11.14; PyMuPDF 2.1; python-docx 1.2.0; NumPy 2.3.3; scikit-learn 1.8.0; PyTorch 2.15.0; Transformers 5.24.1; Sentence Transformers 6.3.0; faster-whisper 1.2.1; CTranslate2 4.9.1; pytest 9.1.1; FFmpeg 9.0.2.

- `.venv/bin/python -m pytest -q` → **18 passed, 5 warnings, exit 0** (20.49 seconds). Warnings were non-failing PyMuPDF/SWIG deprecation notices.
- `.venv/bin/python run_integrity_check.py --input_dir ./sample_submissions --output_dir ./reports --reference_dir ./reference_data --verbose` → **exit 0**. It processed 13 supported submissions, reported 1 per-file extraction failure, 2 empty/no-speech files, and skipped 3 unsupported files.
- The three skips were `sample_submissions/.DS_Store`, `sample_submissions/video/.DS_Store`, and `sample_submissions/dataset_manifest.json`. This contradicts the current README and EVALUATION statement that only the manifest file is skipped.
- Logs confirmed MiniLM loaded on CPU. It also loaded with `HF_HUB_OFFLINE=1`; embedding shape was 384. The Hub emitted non-fatal requests for optional files and an unauthenticated-request notice.
- Logs confirmed faster-whisper processed 14.42 seconds of audio, detected English, and produced timestamped speech segments. The individual video report says `transcription_status: transcribed`; the silent video says `silent` and Whisper was not invoked.
- The corrupt PDF failed independently. The empty PDF and silent clip received empty/no-speech reports; processing continued.
- Report verification found 13 matching manifest IDs with an individual JSON and Markdown report each, aggregate JSON/Markdown, a 14×14 CSV including header, and no match entry lacking a passage or location.

## Architecture and execution flow

1. `run_integrity_check.py:main` checks the input directory, separates recognized extensions from unsupported files, constructs `Config`, and calls `run_pipeline`. It treats individual extraction failures as handled outcomes and returns 0 after a completed batch; fatal pipeline exceptions return 1.
2. `src/pipeline.py:discover` recursively selects `.pdf`, `.docx`, and `.mp4`; `discover_skipped` collects all other files. `extract_document` creates a common document object with source segments and warnings.
3. `remove_repeated_template_sentences` strips only exact recurring sentences containing the hard-coded synthetic/template markers. `chunk_document` chunks PDF pages and DOCX segments separately; for audio it joins Whisper segments while retaining segment time bounds.
4. `Embedder` loads `sentence-transformers/all-MiniLM-L6-v2` and returns normalized 384-dimensional vectors. If model construction fails, it logs the exception and fits/transforms with scikit-learn TF-IDF. `cosine_matrix` computes a full dense chunk-by-chunk cosine matrix.
5. `pipeline._combined_score` uses `0.8 * vector cosine + 0.2 * pairwise TF-IDF cosine`; results below the CLI threshold (default 0.60) are discarded. The pipeline excludes same-document comparisons, assigns exact-copy/semantic/cross-modal categories, adds local-reference matches, aggregates chunk matches into document coverage, calculates a separate AI heuristic, then assigns LOW/MEDIUM/HIGH from peer/reference coverage.
6. `reporter.write_report` writes individual JSON/Markdown reports. `write_aggregate` writes batch counts and a document matrix. `scripts/evaluate.py` compares report pairs with the synthetic manifest and writes `reports/evaluation_metrics.json`.

“Cross-modal” here means **PDF/DOCX text compared with a Whisper transcript**. The code does not analyze video frames or perform a single joint audio/video/text model inference.

## File-by-file implementation review

### Entry point and configuration

- `run_integrity_check.py` — CLI options, directory validation, progress, skipped-file reporting, nonfatal per-file error handling, and exit codes. It does not validate threshold range, chunk size/overlap consistency, device support, or reference schema. No supported files returns 2 without an aggregate report.
- `requirements.txt` — direct package versions are pinned, including the model and ASR stack. There is no full transitive lock or hashes; reproducibility still depends on compatible platform wheels and model revisions/caches.
- `src/__init__.py` — package marker/docstring only.
- `src/config.py` — dataclass defaults (threshold 0.60, 300-token chunks, 45-token overlap, CPU, batch 32). `ai_medium` and `ai_high` are currently unused. The threshold comment says “calibrated” on generated pairs; in practice this is same-corpus tuning, which is evaluation leakage rather than independent calibration.

### Extraction, normalization, and chunking

- `src/extractors.py:extract_document` — PyMuPDF page text extraction; python-docx paragraph/table-row extraction; FFmpeg downmix/resample to mono 16 kHz WAV; silence detection; cached faster-whisper tiny inference; Whisper segment text/start/end metadata. Errors are caught per file. OCR is not implemented. The silence detector reads and unpacks the whole temporary WAV into memory. FFmpeg calls have no timeout or resource/input-size limits.
- `src/normalizer.py:normalize_text` — strips soft hyphens and collapses whitespace. `remove_repeated_template_sentences` removes exact recurring sentences only when they contain one of three fixed markers. It is not a general repeated-header/footer detector and will not recognize unmarked boilerplate.
- `src/chunker.py:chunk_document` — creates chunks with IDs and page/paragraph/table metadata, default overlap, and combined timestamp ranges for Whisper segments. Page and paragraph segments are chunked separately, so content across page/paragraph boundaries is never joined. For a chunk splitting inside a single Whisper segment, the recorded range is the original segment’s full start/end, not word-level timing.

### Embeddings, similarity, and matching

- `src/embeddings.py:Embedder` — primary MiniLM loader; verified successful in this environment and in offline-cache mode. On any constructor exception it logs the full exception and uses corpus-fitted TF-IDF, explicitly recording the backend/error. In fallback mode the 0.8 term is also TF-IDF vector cosine, so the score is lexical twice, not semantic-plus-lexical.
- `src/indexer.py:NumpyIndex` — normalizes and searches vectors, but the production pipeline never calls it. It is currently unused; search returns vector row indexes rather than the associated `items` values and does not exclude self/same-document hits.
- `src/similarity.py:cosine_matrix` — normalizes vectors and returns a dense full pair matrix; `lexical_score` fits a new two-document TF-IDF vectorizer for each compared pair. The latter is supplementary, but repeated vectorizer fitting is expensive.
- `src/pipeline.py:_combined_score`, `run_pipeline`, `_deduplicate` — performs all chunk pairs using the dense matrix and nested loops. This is quadratic in chunk count in both memory and work. Deduplication keys on matched document and the first 120 characters of the query passage, not stable chunk IDs. `document_id` is only `Path.stem`; two files with the same basename in different folders can overwrite reports and make aggregate IDs ambiguous.
- `src/explainability.py:make_match` — keeps the query/source text, cosine values, combined score, and locations. It labels the vector kind correctly in the explanation. However `src/reporter.py:write_report` separately prints every vector score as “semantic cosine,” even when the report is using the TF-IDF fallback. This is a concrete misleading-output bug.
- `src/external_checker.py:load_references` — loads local JSON but silently returns an empty list on missing/invalid JSON. It does not validate each reference’s schema. `source_url` and reference title/source name are not carried into the match evidence shown to reviewers. The supplied one-item corpus is synthetic; in this run all external match lists were empty, so a positive external match was not demonstrated.

### AI indicator and reporting

- `src/ai_detector.py:analyze_ai` — uses sentence-length variation, type/token ratio, and repeated-bigram rate in a fixed formula. It is not trained or calibrated. The key name `ai_generated_probability` can be mistaken for a probability despite the explanation; it is only a heuristic score. It imports unused `Counter`/`math` symbols. Short inputs return 0, which means “insufficient text” rather than evidence of human authorship.
- `src/reporter.py:write_report` — creates report files and aggregate summary. It repeats multimodal matches under both peer and multimodal sections, hard-codes the “semantic cosine” label mentioned above, and assumes all report fields exist. `write_aggregate` creates readable counts but has a grammar issue (“1 extraction failures”).

### Scripts, tests, data, and documentation

- `scripts/generate_dataset.py` — creates 6 PDFs, 5 DOCX files, a local Samantha/espeak speech sample and a silent MP4, plus a malformed PDF and manifest. It writes a `.DS_Store`-agnostic dataset; the existing `.DS_Store` files are filesystem artifacts, not generated examples. TTS generation is macOS/Linux-engine dependent.
- `scripts/evaluate.py` — computes 78 unordered pairs from 13 report IDs and manifest relationships. It maps any reported `semantic` category to the “paraphrase” evaluation class, and uses the strongest report match per document pair. It does not check that all expected manifest IDs have reports, and it relies on existing `reports/` files rather than invoking the pipeline itself.
- `tests/test_chunker.py` — chunk overlap/page metadata and adjacent timed-segment bounds.
- `tests/test_cli.py` — valid PDF plus corrupted PDF/unsupported extension; checks exit 0 and aggregates.
- `tests/test_edge_cases.py` — silent audio detection and MP4 without audio; the CLI suite also covers malformed PDF. No large-file, timeout, duplicate-basename, invalid-configuration, or malformed-reference tests.
- `tests/test_embeddings.py` — real MiniLM 384-dimension/paraphrase ranking when the model loads (otherwise skipped) and a forced TF-IDF fallback ranking test.
- `tests/test_extractors.py` — PDF/DOCX, corrupt/empty PDF, invalid extension, actual speech transcription, text contents, and timestamps.
- `tests/test_normalizer.py` — marked template sentence removal while retaining analytical text/location.
- `tests/test_pipeline.py` — self-match exclusion, two sample paraphrase pairs, and PDF-to-spoken-MP4 matching.
- `tests/test_similarity.py` — cosine/index behavior and lexical-overlap signal. It does not test real external-reference matching.
- `sample_submissions/` — 6 PDFs, 5 DOCX, 2 MP4; includes corrupted and empty PDF and silent clip. The DOCX/PDF paraphrase examples share identical paraphrase text, so they test an exact inter-document duplicate as well as source-to-paraphrase matches.
- `sample_submissions/dataset_manifest.json` — 13 IDs, 10 positive pairs, and 5 boilerplate-only controls. The positives are intentionally derived from a few passages and their copies/paraphrases/transcripts.
- `reference_data/references.json` — one synthetic reference with `source_url: null`; not a reusable web corpus.
- `reports/` — 13 individual JSON and 13 individual Markdown reports, aggregate JSON/Markdown, CSV matrix, and evaluator JSON. The current JSON contains only generated synthetic data. If real submissions are ever processed, these reports would contain extracted student text; `.gitignore` does not exclude `reports/`.
- `README.md` — describes architecture, setup, limitations, and scaling. Its stated batch skip count is stale: it says only the manifest is skipped; this run skips the manifest plus two `.DS_Store` files.
- `EVALUATION.md` — correctly warns that the set is synthetic, but its CLI summary also says only one unsupported file is skipped. It should reflect the actual three skips and current run; do not interpret the perfect scores as external validity.
- `.gitignore` — excludes Python caches, venv, and models, but not `.DS_Store` or generated reports/data. Repository currently has no commits and no LICENSE file.
- Root `.DS_Store` — Finder metadata, not a project artifact; currently unignored.

## Independent evaluation check

I independently formed the set of expected unordered pairs from `dataset_manifest.json` and the set of predicted unordered pairs from all 13 individual JSON reports, then computed the confusion counts directly. This reproduced `scripts/evaluate.py`:

| Item | Result |
|---|---:|
| Submission IDs / candidate pairs | 13 / 78 |
| Expected / predicted positive pairs | 10 / 10 |
| TP / FP / FN / TN | 10 / 0 / 0 / 68 |
| Precision / recall / F1 | 1.00 / 1.00 / 1.00 |
| Exact-copy pairs detected | 2 / 2 |
| Paraphrase pairs detected | 4 / 4 |
| Cross-modal pairs detected | 4 / 4 |
| Boilerplate control false positives | 0 / 5 |

The arithmetic is reproducible. The inference that the model will achieve these rates on real student work is **not** supported: the threshold and examples are chosen from the same synthetic corpus, the corpus contains only a few related passages, and there is no independent hold-out set or real review population. The 100% values are smoke-test results, not a performance claim.

## Assignment compliance

| Requirement | Status | Evidence / caveat |
|---|---|---|
| PDF extraction with page numbers | PASS | `src/extractors.py`; empty/corrupt cases are isolated. No OCR for scans. |
| DOCX paragraphs and tables | PASS | `src/extractors.py`; paragraph/table row metadata retained. |
| MP4 audio extraction and Whisper timestamps | PASS | FFmpeg + faster-whisper `tiny`; real generated sample was transcribed in this run. |
| 10–15 synthetic submissions; ≥5 PDF, ≥5 DOCX, 2–3 MP4 | PASS | 13 total: 6 PDF, 5 DOCX, 2 MP4. |
| MiniLM 384-dimensional semantic embeddings | PASS | Verified `all-MiniLM-L6-v2`, CPU, 384-D, also offline from cache. |
| TF-IDF fallback / lexical cosine | PASS | Implemented and tested; fallback is explicitly lexical, not semantic. Markdown fallback label is wrong. |
| Combined scoring, thresholding, exact/paraphrase comparison | PASS (prototype) | 0.8/0.2 rule, threshold 0.60; sample test pairs pass. Threshold is tuned on the same sample set. |
| Boilerplate suppression | PARTIAL | Exact marked synthetic sentences and short fragments suppressed; not general boilerplate/header detection. |
| Cross-document / cross-modal comparisons | PASS (narrow) | Text chunks compared; MP4 means transcript text, not visual video analysis. |
| External references | PARTIAL | Local JSON path works in code, but only one synthetic reference and no positive-match regression test. No web search. |
| AI-generated content indicator | PARTIAL | Documented uncalibrated language heuristic only; not authorship detection. |
| Explainable passages and locations | PASS (with defect) | Excerpts, pages, transcript ranges; Markdown mislabels fallback vector cosine as semantic. |
| Per-file JSON/Markdown and aggregate outputs | PASS | 13 individual pairs plus aggregates and matrix were verified. |
| Evaluation and failure analysis | PARTIAL | Metrics reproduce; same-set threshold selection and synthetic-only positives make general claims invalid. |
| CLI and per-file continuation | PASS | Full run exits 0 despite handled corrupt PDF; current run reports three unsupported artifacts. |
| 10,000-document architecture brief | PARTIAL | README contains a plausible plan; PostgreSQL/Qdrant/HNSW/queues/caching are proposals, not implemented. Dense all-pairs matrix does not scale. |
| Public GitHub readiness | PARTIAL / NOT YET | No LICENSE or commits; `.DS_Store` files unignored; README/EVAL skip count stale; reports are not ignored. |

## Weaknesses and recommended fixes (ranked)

### P0 — before describing this as a real integrity detector

1. **Create an independent evaluation set and freeze threshold selection.** Keep the current set as a smoke test; use held-out paraphrases, unrelated lookalikes, multiple boilerplate styles, and cross-modal clips. Record the threshold before scoring the hold-out. Report confidence intervals and chunk-level as well as pair-level outcomes.
2. **Fix report identity and backend labeling.** Use collision-resistant document IDs or relative-path IDs and reject duplicates. In `src/reporter.py`, render the match’s `vector_similarity_kind` instead of always calling it semantic cosine. Test both semantic and fallback report text.
3. **Prove external-reference behavior.** Add a positive synthetic reference example and tests for missing, malformed, and wrong-schema reference JSON. Surface “reference corpus unavailable/empty” separately from “no match found.” Include title/source/URL fields in external-match evidence where present.

### P1 — before public GitHub submission

4. Add a suitable `LICENSE`, commit a clean snapshot, remove `.DS_Store`, add it to `.gitignore`, and reconcile README/EVALUATION against the actual three skipped files. Decide whether synthetic reports should be tracked; exclude reports containing real student content and document that privacy rule.
5. Validate CLI parameters (`threshold` 0–1, positive chunk size, overlap less than chunk size, supported device). Add resource controls/timeouts and file-size limits around FFmpeg/document processing; submissions are untrusted inputs and currently have no timeout/resource limit.
6. Make report JSON/Markdown schema validation a test and have `scripts/evaluate.py` fail loudly on missing/extra IDs, stale reports, duplicate pairs, or unsupported relationship categories.

### P2 — architecture and maintainability

7. Avoid full dense `N×N` chunk similarity for large corpora; batch, prefilter candidates, and actually integrate an approximate-nearest-neighbor index. `src/indexer.py:NumpyIndex` currently is unused and does not return its `items` mapping.
8. Add general repeated-header/footer and boilerplate logic, but evaluate it carefully against meaningful repeated analysis. Keep the current marker-specific behavior as a transparent baseline.
9. Format the CLI, tests, and smaller modules consistently; remove unused imports and add type annotations/docstrings. Use a transitive lock or tested constraints if reproducible installs are a submission goal.

## Blunt readiness verdict

**Not yet ready as a public submission without cleanup and caveats.** It is ready to demonstrate as a local prototype: the core semantic/transcription path runs, results are explainable, and handled input failures do not stop the batch. The perfect metrics are synthetic-set smoke-test results. Before submission, prioritize (1) independent evaluation, (2) report correctness/document identity plus an external positive test, and (3) GitHub hygiene/license/ignored metadata and accurate docs. Do not describe it as a proven plagiarism or AI-writing detector.

## Implementation follow-up — 25 November 2026

The requested fixes were implemented after the read-only audit. This section supersedes the readiness statuses above where noted; the original audit observations are retained as the baseline.

### Resolved and verified

1. **Evaluation split:** added `scripts/generate_holdout.py` and a separate five-submission fictional hold-out under `evaluation/holdout_submissions`. It covers an original, exact copy, paraphrase, unrelated control, and generated spoken MP4. The unchanged threshold `0.60` was used. The evaluator now requires report IDs to match the manifest exactly and records split name, threshold, confusion counts, overall metrics, one-vs-rest exact/paraphrase/cross-modal metrics, and designated boilerplate-control results. `EVALUATION.md` distinguishes the original development numbers from hold-out results and states the synthetic-data limitations.
2. **Report scoring and identity:** Markdown now describes individual vector scores as “MiniLM semantic cosine” or “TF-IDF vector cosine (lexical only)” based on actual backend, and identifies the combined score method. Duplicate case-insensitive filename stems receive sanitized relative-path IDs with a SHA-256 suffix. JSON and Markdown link to the original submission; peer-match evidence also links to the matched submission. Relative paths are stored to avoid exposing the local account path.
3. **External-reference evidence:** peer/reference match reports carry reference title, source name, and URL metadata. A real-pipeline regression test checks one positive synthetic reference, verifies its ID and passage, and confirms unrelated text has no external match.
4. **Boilerplate controls:** repeated long exact sentences shared by at least three files and at least half of a batch are removed as likely boilerplate; the previous marked-template behavior remains. Hold-out controls share an administrative sentence and generated results contained zero false positives among three designated controls. This heuristic remains conservative and imperfect.
5. **Release hygiene:** added the MIT license; `.gitignore` now excludes OS metadata, virtual environments, caches, temporary/runtime outputs, reports, and conventional private student-submission folders. Removed the existing `.DS_Store` files from the sample tree. README and EVALUATION now report one unsupported manifest JSON per run. A text scan of synthetic PDF/DOCX/JSON inputs and reports found no local username/path.

### Measured results from the completed rerun

- Automated suite at that follow-up: **21 passed, 5 warnings** (non-failing PyMuPDF/SWIG deprecations); compileall succeeded. This intermediate count is superseded by the assignment-compliance rerun below.
- Development at that follow-up: 13 supported submissions, 78 pairs, TP/FP/FN/TN `10/0/0/68`, precision/recall/F1 `1.000/1.000/1.000`; exact 2/2, paraphrase 4/4, cross-modal 4/4; 0/5 boilerplate-control false positives. The later compliance rerun adds the second spoken MP4 and updates these results below.
- Hold-out: 5 submissions, 10 pairs, TP/FP/FN/TN `6/0/0/4`, precision/recall/F1 `1.000/1.000/1.000`; exact 1/1, paraphrase 2/2, cross-modal 3/3; 0/3 control false positives. CLI exit 0; no per-file failures and one unsupported manifest skipped.
- All 13 development and 5 hold-out submissions at that follow-up had individual JSON/Markdown reports. The latest counts are recorded below.

### Unresolved findings and release caveats

- Both datasets are small fictional examples. Hold-out results are independent of the threshold decision but still contain only six positives and four negatives, with related pairs sharing source content. The 100% rates are not a reliable estimate for real academic work.
- The 0.60 threshold was previously informed by the development examples; only the hold-out remained untouched. A larger independently authored or adjudicated validation set is needed before setting an operational threshold.
- `external_checker.load_references` still silently treats missing or malformed JSON as an empty corpus and does not validate every reference schema. Positive matching is now demonstrated, but robust unavailable/error status and malformed-reference tests remain.
- There is still no OCR, comprehensive resource/time limit for untrusted inputs, or general detector for paraphrased/common assignment boilerplate. Repeated exact-sentence filtering can remove meaningful repeated content.
- Dense all-pairs chunk similarity remains quadratic and is not suitable for large batches. The AI indicator remains an uncalibrated writing-style heuristic.
- The repository has not been committed or published. The files now have release hygiene and a license, so it can be submitted publicly as a clearly labelled prototype after the user reviews the diff; it is not ready to claim validated plagiarism detection or to process real student work without privacy and operational safeguards.

## Original assignment compliance verification — 25 November 2026

This latest pass re-read the original assignment brief and supersedes the intermediate implementation-follow-up counts above.

### Verified requirements

- **Source structure and CLI:** required modular `src/` files, runner, requirements, sample data, references, scripts, tests, reports, README, and evaluation are present. The original CLI flags remain supported; additional risk-band flags are optional. Per-file failures are isolated and a completed batch exits 0.
- **Ingestion and locations:** PyMuPDF extracts page-level PDF text; python-docx extracts paragraphs/table rows; FFmpeg and faster-whisper tiny extract/transcribe MP4 speech and retain actual segment times. Empty/corrupt PDFs, silent clips, and no-audio MP4s have regression coverage. OCR is explicitly not claimed.
- **Chunking and metadata:** default chunk size is 300 whitespace-delimited tokens (within 200–400), overlap is 45, and chunk IDs, document IDs, filenames, page/paragraph/table or timestamp metadata are preserved. Tests cover overlap, default range, and locations.
- **Embeddings/index/matching:** MiniLM all-MiniLM-L6-v2 is primary and returns normalized 384-D vectors. The fixed NumPy exact index maps vectors to chunk records and computes cosine matrix scores. Internal comparisons exclude same-document pairs. Exact copies, both garden paraphrase pairs, five development cross-modal relationships, and an external-reference positive/negative regression are verified. TF-IDF remains a clearly labelled fallback and supplementary signal.
- **Signals, reports, and boilerplate:** peer, local-reference, and AI-style signals are separate. Risk coverage bands (MEDIUM 10%, HIGH 25%) are configurable. Match reports include excerpts, locations, source links, and scoring backend. Repeated boilerplate filtering uses corpus frequency plus template/administrative cues and preserves repeated analytical text without those cues; unmarked boilerplate remains a limitation.
- **Dataset:** 14 supported samples: 6 PDFs, 5 DOCX, 3 MP4 (two 10–30 second spoken English TTS clips plus one 12-second silent control). The manifest IDs match files and lists exact/paraphrase/cross-modal labels and the corrupt PDF, empty PDF, and silent MP4. It also identifies the LLM-style sample and independent originals. This resolves the speech-versus-silent-case tension with two speech clips and one explicitly degraded clip.
- **Documentation/deliverables:** README has a pipeline diagram, single-command Python setup (FFmpeg is a documented system prerequisite), model-download behavior, sample CLI output, scoring math/limitations, AI disclosure, and the 10,000-document queue/worker/storage/index/cache/cost/monitoring plan. EVALUATION contains measured results, failure/ambiguity cases, and embedding/index trade-offs.

### Final measured verification

- `.venv/bin/python -m compileall -q src scripts tests`: succeeded.
- `.venv/bin/python -m pytest -q`: **28 passed, 5 warnings** (non-failing PyMuPDF/SWIG deprecations).
- Development CLI: exit 0; 14 supported files, 1 corrupt-PDF extraction failure, 2 empty/no-speech files (empty PDF and silent MP4), 1 unsupported manifest skipped. Ground truth: 91 pairs, 11 positives; TP/FP/FN/TN `11/0/0/80`; precision/recall/F1 `1.000/1.000/1.000`; exact 2/2, paraphrase 4/4, cross-modal 5/5; 0/5 boilerplate-control false positives.
- Hold-out CLI: exit 0; 5 supported files, no extraction failures, 1 unsupported manifest skipped. Ground truth: 10 pairs, 6 positives; TP/FP/FN/TN `6/0/0/4`; precision/recall/F1 `1.000/1.000/1.000`; exact 1/1, paraphrase 2/2, cross-modal 3/3; 0/3 boilerplate-control false positives. Threshold remained 0.60 and was not tuned on hold-out.
- All 14 development and 5 hold-out submissions have JSON and Markdown reports. Matrices are 15×15 and 6×6 including headers, symmetric, with aggregate reports present. Every original and peer-source link resolves; every match includes excerpts and locations. The two spoken development MP4s and hold-out MP4 show completed English transcription and timestamped cross-modal matches. All three development MP4s are 10–30 seconds.
- Generated input/report scans found no local account path. Default reports, caches, environments, OS metadata, and conventional private-submission directories are ignored by Git.

### Remaining limitations

- The synthetic sets are tiny and pair-dependent. Perfect measured metrics do not estimate real academic-integrity performance; development threshold selection remains in-sample and labels were not independently adjudicated.
- The sample local reference corpus is synthetic and narrow. Malformed/missing reference data is warned and skipped, but the pipeline does not have a rich corpus-availability state or internet search.
- Scanned PDFs lack OCR; file-size, CPU, memory, and subprocess-time limits for untrusted inputs are incomplete.
- Dense exact comparisons still require quadratic score-matrix memory. HNSW/Qdrant/Milvus are documented future architecture, not implemented production infrastructure.
- The AI score is an uncalibrated style heuristic. General boilerplate detection can miss unmarked/paraphrased instructions; reviewer context remains necessary.
- The repository has not been committed or published. It meets the assignment as a synthetic local prototype, but is not a validated integrity detector and should not be used as an automated misconduct decision system.

## Current publication status

As of 26 November 2026, the prior MIT license was removed because its copyright attribution could not be substantiated. No license has been selected; README and release notes state this explicitly. The older MIT-related observations above record the historical audit/fix sequence and do not describe the current license status.
