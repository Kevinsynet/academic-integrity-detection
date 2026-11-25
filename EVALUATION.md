# Evaluation and verification

## Dataset and method

The development set contains 14 fictional submissions: 6 PDFs, 5 DOCX files, and 3 MP4s. Two MP4s contain 10–30 seconds of English TTS speech; the third is a 12-second silent degraded control. The set includes exact copies, paraphrases, two text-to-speech cross-modal relationships, independent originals, an LLM-style synthetic sample, five boilerplate-control pairs, a corrupt PDF, an empty PDF, and the silent clip. `sample_submissions/dataset_manifest.json` records the expected relationships and known degraded files.

The separate hold-out set contains five independently authored fictional examples (10 candidate pairs). Both splits were scored at the unchanged threshold **0.60** with MiniLM and the combined score `0.8 × MiniLM cosine + 0.2 × pairwise TF-IDF cosine`. The development threshold was informed by the original synthetic examples; only the hold-out was kept out of threshold selection. Neither split includes real student work.

The evaluator builds all unordered candidate pairs from the manifest and requires exact equality between manifest IDs and report IDs. A pair is predicted positive when at least one peer match was reported. Scenario metrics are one-vs-rest pair metrics across the full candidate universe. Confusion matrices use actual labels as rows and predictions as columns: `[[TP, FN], [FP, TN]]`. Boilerplate specificity is also measured separately over the designated negative-control pairs.

Document risk bands use the greater of peer-match coverage and external-reference coverage: MEDIUM begins at 10%, HIGH begins at 25%, and these two values can be configured from the CLI. The AI heuristic is reported independently and does not affect integrity risk.

The AI-style indicator is reproducible but uncalibrated: for at least 20 words it clips `0.30 × (1 − min(1, sentence_length_CV)) + 0.35 × (1 − type_token_ratio) + 0.35 × min(1, 4 × repeated_bigram_rate)` to `[0, 1]`; shorter inputs receive 0 with an insufficient-text note. It is not authorship evidence.

## Actual results

### Development

The completed run produced 91 candidate pairs and 11 labelled positives.

| Measure | Result |
|---|---:|
| TP / FP / FN / TN | 11 / 0 / 0 / 80 |
| Confusion matrix | `[[11, 0], [0, 80]]` |
| Precision / recall / F1 | 1.000 / 1.000 / 1.000 |
| Exact-copy | 2/2 detected; P/R/F1 1.000/1.000/1.000 |
| Paraphrase | 4/4 detected; P/R/F1 1.000/1.000/1.000 |
| Cross-modal | 5/5 detected; P/R/F1 1.000/1.000/1.000 |
| Boilerplate controls | 0 false positives across 5 controls; specificity 1.000 |

These are development-set results and are in-sample: the default threshold had been informed by the earlier small synthetic development corpus.

### Independent synthetic hold-out

The hold-out contains 10 candidate pairs and 6 labelled positives. It was scored at the same fixed threshold, with no threshold selection based on hold-out results.

| Measure | Result |
|---|---:|
| TP / FP / FN / TN | 6 / 0 / 0 / 4 |
| Confusion matrix | `[[6, 0], [0, 4]]` |
| Precision / recall / F1 | 1.000 / 1.000 / 1.000 |
| Exact-copy | 1/1 detected; P/R/F1 1.000/1.000/1.000 |
| Paraphrase | 2/2 detected; P/R/F1 1.000/1.000/1.000 |
| Cross-modal | 3/3 detected; P/R/F1 1.000/1.000/1.000 |
| Boilerplate controls | 0 false positives across 3 controls; specificity 1.000 |

The hold-out content and outputs are in `evaluation/holdout_submissions` and `evaluation/holdout_reports`. Its spoken MP4 was processed by faster-whisper and has timestamped cross-modal matches. The independent set is small and related by shared source passages; these metrics are controlled regression evidence, not a real-world performance estimate.

## External-reference check

`test_external_reference_positive_evidence_and_negative_control` sends a synthetic exact reference passage and unrelated text through the actual pipeline. It verifies the expected reference ID, matching excerpt, and title for the positive sample, and no external match for the unrelated control. This verifies local-corpus functionality only; the checker does not search the internet.

## Observed failure and ambiguous cases

1. **Corrupt PDF:** `sample_submissions/pdf/corrupted.pdf` fails extraction with a PyMuPDF `FileDataError`. The pipeline records an error and report for that file and continues processing the batch.
2. **Empty and silent media:** the empty PDF yields no text; the silent MP4 is detected before Whisper inference and is reported as empty/no-speech. Both cases are represented as degraded files in the manifest rather than successful content analysis.
3. **ASR wording ambiguity:** Whisper transcribed the generated river clip’s “river monitoring group” as “river monitor in group” in the observed run. The remaining sentence was recognized and matched to the source document, but this wording difference shows why reviewers must check audio when exact wording matters.
4. **Ground-truth ambiguity:** `coastal_paraphrase.pdf` and `garden_paraphrase.docx` contain the same paraphrase text. Their inter-document relationship is therefore an exact copy, even though each is also a paraphrase of the garden original. They are not independent paraphrase examples.

## Embedding and vector-index trade-offs

The pipeline uses normalized 384-dimensional MiniLM vectors in an exact NumPy in-memory index. The vectorized dense cosine matrix gives exact scores and is simple to reproduce for small batches, but its all-pairs memory grows quadratically with the number of chunks. MiniLM captures meaning-preserving rewrites better than lexical counts, at the cost of PyTorch runtime, model download/cache storage, and CPU inference. If MiniLM cannot load, TF-IDF keeps the pipeline functional but is lexical-only and can miss paraphrases. At larger scale, Qdrant or Milvus with HNSW can reduce candidate-search time and avoid a full dense matrix; approximate retrieval trades some recall for speed and requires index memory and operational monitoring. A production system should retain an exact Flat path for evaluation and rerank HNSW candidates using exact cosine and lexical scores.

## Final verification run

- A fresh Python 3.11 virtual environment was created outside the repository and installed from `requirements.txt`; `pip check` reported no broken requirements.
- `python -m compileall -q src scripts tests run_integrity_check.py` succeeded in that environment.
- `python -m pytest -q` → **28 passed, 5 warnings**. The warnings are non-failing PyMuPDF/SWIG deprecations.
- Development CLI exited 0, processing 14 supported submissions with 1 corrupt-PDF extraction failure, 2 empty/no-speech inputs (the empty PDF and silent MP4), and 1 unsupported manifest JSON skipped.
- Hold-out CLI exited 0, processing all 5 supported submissions with no extraction failures and skipping its 1 manifest JSON.
- All 14 development and 5 hold-out IDs have individual JSON and Markdown reports. The matrices are 15×15 and 6×6 including headers; aggregate summaries and evaluator JSON were regenerated.
- Every report’s original-submission link was checked against the generated inputs; aggregate counts and report IDs match. Sample document text and reports were checked for local absolute paths, credential patterns, and personal identifiers; none was found.
- Both spoken development MP4s were transcribed by Whisper and their reports contain cross-modal matches with start/end time ranges. Separate tests verify transcript text and timestamp bounds; silent and missing-audio cases are covered as empty outcomes or extraction errors.

## Limitations

The hold-out has only six positives and four negatives, with related pairs sharing a small number of source passages. Labels were written with the fictional examples rather than independently adjudicated. The threshold is not hold-out-tuned, but its historical development-set selection remains a source of optimism. The perfect metrics therefore do not estimate performance on real academic work.

Boilerplate filtering uses frequency plus recognizable administrative/template cues and preserves repeated analytical findings without those cues. It can miss unmarked or paraphrased prompts, and it may suppress genuinely repeated template-like material. The AI-writing score is an uncalibrated linguistic heuristic, not authorship evidence. The external corpus is local and synthetic. Scanned PDFs are not OCR'd; large/untrusted inputs lack robust resource limits; chunk matching is quadratic and intended only for small batches. Reviewers must inspect passages and original media before drawing conclusions.
