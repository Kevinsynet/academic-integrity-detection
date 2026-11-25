# Interview Preparation — integrity-detection

## A concise project explanation

**30–45 second introduction:**

> I built a local Python prototype that screens PDF, DOCX, and MP4 submissions for possible content overlap. It extracts text and source locations, transcribes MP4 speech with faster-whisper, chunks the text, and compares passages with MiniLM embeddings plus a smaller TF-IDF lexical signal. It writes JSON and Markdown evidence reports. The current synthetic batch demonstrates exact-copy, paraphrase, and transcript-to-PDF matching, but the 100% pair metrics are only smoke-test results on a tiny hand-constructed dataset. I would not use this as proof of misconduct or as a reliable AI-writing detector.

## Walk through the actual architecture

1. `run_integrity_check.py:main` accepts the input and output directories, threshold, chunk settings, device, reference directory, and `--skip_video`. It reports unsupported files and returns success when a batch completes despite an isolated bad file.
2. `src/pipeline.py:discover` selects PDF, DOCX, and MP4 inputs. `src/extractors.py:extract_document` reads PDF text page by page with PyMuPDF, DOCX paragraphs and table rows with python-docx, or extracts mono 16 kHz WAV from MP4 with FFmpeg before faster-whisper transcription.
3. Each extracted source segment retains its page, paragraph/table row, or Whisper start/end time. `src/normalizer.py` frequency-filters repeated sentences only when they have recognizable template/administrative cues, preserving repeated analytical sentences without those cues. `src/chunker.py` builds 300-token chunks with 45-token overlap and joins adjacent Whisper segments.
4. `src/embeddings.py:Embedder` loads `sentence-transformers/all-MiniLM-L6-v2`, which returns 384-dimensional normalized vectors. If model construction fails, the code records the exception and labels a scikit-learn TF-IDF fallback as lexical-only.
5. `src/indexer.py:NumpyIndex` stores normalized vectors and chunk items; its exact matrix multiplication produces cosine values. The decision score in `src/pipeline.py:_combined_score` is `0.8 × vector cosine + 0.2 × pairwise TF-IDF cosine`. When MiniLM is active, the first term is semantic; in fallback mode it is also TF-IDF-based, so the score must not be described as semantic.
6. Candidate matches retain the two excerpts, locations, score breakdown, and category. `src/reporter.py` writes individual and aggregate reports. `scripts/evaluate.py` compares predicted document pairs with labels in `sample_submissions/dataset_manifest.json`.

“Cross-modal” here is text-to-text across input types: PDF/DOCX extracted text compared with Whisper transcript text. It is not video-frame/image analysis or a joint multimodal model.

## Core ideas in beginner-friendly language

### What are embeddings?

An embedding is a list of numbers that represents a passage. MiniLM maps a sentence to 384 numbers so that passages with similar meaning often point in similar directions. In the actual report, `garden_original.pdf` and `coastal_paraphrase.pdf` had a MiniLM cosine of **0.7801** even though their pairwise lexical score was only **0.0715**. That is why an embedding can find a paraphrase that does not reuse many exact words. It can still make mistakes; the number is evidence to review, not a verdict.

### Why MiniLM?

`all-MiniLM-L6-v2` is compact enough for CPU inference and produces fixed-size sentence vectors. It is the real primary model in this environment; it loaded from the local Hugging Face cache even with `HF_HUB_OFFLINE=1`. Its 384 dimensions are a design trade-off between useful semantic representation and model size/latency. A different model or domain may score passages differently.

### What does TF-IDF do?

TF-IDF gives more weight to words that matter to a document and less weight to words common across the compared texts. `src/similarity.py:lexical_score` fits a TF-IDF vectorizer to a pair of passages and calculates their cosine. It can support exact or near-exact overlap. It is not a language-understanding model, and in fallback mode the pipeline uses TF-IDF for both the vector and lexical parts.

### What is cosine similarity?

Cosine compares the angle between two vectors. A value near 1 means the vectors point in similar directions, near 0 means little alignment, and negative values indicate opposing directions (the current normalized MiniLM outputs in these tests are nonnegative for these examples). Exact copies scored 1.000. A score does not mean “a 78% chance of plagiarism.”

### Why combine semantic and lexical scores?

The current formula weights MiniLM cosine at 80% and pairwise TF-IDF at 20%. Semantic similarity can surface paraphrased meaning; lexical overlap can add evidence of shared wording. In the actual garden paraphrase, semantic similarity carried the match while lexical overlap was low. The default 0.60 threshold was informed by earlier development examples, so development results are in-sample. It was frozen before scoring the separate hold-out and was not tuned on hold-out examples.

### How does Whisper work here?

FFmpeg extracts audio and converts it to a mono, 16 kHz WAV. faster-whisper’s tiny model recognizes speech and returns text segments with start/end times. Both spoken sample MP4s were transcribed as English. The garden transcript covers about 0.0–14.3 seconds and the river transcript about 0.0–17.6 seconds. One observed error rendered “river monitoring group” as “river monitor in group,” so reviewers should check original audio when exact wording matters.

### How does cross-modal matching work?

The software does not directly compare sound waves with PDF characters. Whisper first turns speech into text. The same text chunking and embedding comparison then compares that transcript with PDF/DOCX text. In `reports/garden_original.json`, the PDF excerpt matched the transcript passage at **0.9885 semantic cosine**, **0.8654 lexical cosine**, and **0.9639 combined**, with page 1 on one side and 0.0–14.3 seconds on the other.

### What do precision, recall, and F1 mean?

- **Precision** = true positives ÷ all predicted positives. Development: 11 correct predicted pairs ÷ 11 predicted pairs = 1.00.
- **Recall** = true positives ÷ all labeled positive pairs. Development: 11 detected ÷ 11 expected = 1.00.
- **F1** = harmonic mean of precision and recall, `2PR/(P+R)`. It is 1.00 in this synthetic run.

The development values describe 91 curated pairs from 14 generated documents; the separate hold-out has 10 pairs. Both sets are synthetic and too small to estimate performance on real academic submissions.

### Why is the AI indicator only a heuristic?

`src/ai_detector.py:analyze_ai` combines sentence-length variation, type/token ratio, and repeated-bigram rate using hand-selected coefficients. It has no labeled training set, calibration, or validated author-specific benchmark. Its field name says “probability,” but the value is an uncalibrated style score. Human writing can look regular, and generated writing can look varied.

## Why these technologies were chosen

- **PyMuPDF:** direct page-by-page PDF text and page metadata.
- **python-docx:** paragraphs and table rows without a heavy document-conversion service.
- **FFmpeg:** common local audio extraction/transcoding for MP4.
- **faster-whisper:** local speech recognition, CPU-capable tiny model, and segment timestamps.
- **Sentence Transformers MiniLM:** compact semantic embeddings runnable on CPU.
- **NumPy/scikit-learn:** direct cosine calculations and supplementary TF-IDF, without a database service for a small prototype.
- **JSON/Markdown:** simple machine-readable records plus reviewer-friendly passages.

## 25 likely recruiter questions with honest answers

1. **What does the project do?**

   It screens local PDF, DOCX, and MP4 speech submissions for possible textual overlap, then reports matching passages and locations for human review.

2. **How does a submission move through the system?**

   The CLI discovers files; extractors create page/paragraph/timestamp segments; normalization/chunking prepares text; MiniLM and TF-IDF score cross-document pairs; `reporter.py` writes per-file and aggregate evidence.

3. **What is an embedding in this project?**

   It is a 384-number MiniLM vector for a passage. Cosine similarity compares its direction with another passage vector.

4. **Why MiniLM instead of keyword search?**

   A paraphrase can use different words but preserve meaning. In the sample corpus, the garden paraphrase had semantic cosine 0.7801 and lexical score 0.0715.

5. **What does “384-dimensional” mean?**

   Each passage is represented by 384 numeric coordinates. It is a fixed-size learned representation, not 384 keywords or 384 evidence points.

6. **What does TF-IDF contribute?**

   It scores shared terms and n-grams. Here it is a secondary signal for overlap and also the clearly disclosed fallback if MiniLM cannot load.

7. **How do you interpret cosine 0.78?**

   As a relatively aligned vector pair under this model, not as 78% authorship confidence or a misconduct probability.

8. **Why combine two scores?**

   Embedding cosine is meant to capture semantic similarity; TF-IDF adds word overlap. The code uses an 80/20 weighted sum, which is a prototype heuristic.

9. **Why set the threshold to 0.60?**

   In this synthetic run the lowest labeled positive was 0.626 and the highest designated boilerplate-control negative was 0.364. That is an observed sample separation, not independent calibration.

10. **Why 300-token chunks and 45-token overlap?**

    It gives a compact local comparison unit while retaining boundary context. Page and paragraph boundaries remain attached. These are configurable, not experimentally proven universal settings.

11. **How do you prevent self-matches?**

    `pipeline.run_pipeline` skips comparing a document’s chunk group with itself. The tests assert there are no self-document matches.

12. **How are exact copies different from paraphrases?**

    The report labels high lexical overlap (at least 0.97) as `exact-copy`; other MiniLM-based matches are labeled `semantic`. Those are reviewer labels, not a legal classification.

13. **How does MP4 transcription work?**

    FFmpeg extracts PCM audio, then faster-whisper tiny returns recognized text and segment times. It is local inference after the model is cached/downloaded.

14. **Are the timestamps guessed?**

    The segment start/end values come from faster-whisper. When multiple segments are joined into a text chunk, the chunk keeps the first segment’s start and last segment’s end; it does not invent word-level timestamps.

15. **What does cross-modal mean here?**

    PDF or DOCX text is compared with an MP4 transcript. There is no analysis of visual frames and no direct audio-embedding comparison.

16. **How is boilerplate handled?**

    It counts exact template/administrative sentences across the batch and removes them only after the frequency threshold and recognizable cue check. Repeated analytical sentences without those cues are preserved. Unmarked or paraphrased boilerplate can still pass through.

17. **What was the evaluation result?**

    Development: 11 labeled pairs detected among 91 candidates, TP 11, FP 0, FN 0, TN 80. The separate hold-out had 6/6 positives among 10 candidate pairs. Both are small synthetic regression sets, not real-world accuracy.

18. **Why is 100% F1 not proof of quality?**

    The hold-out was kept out of threshold selection, but it has only six positives and four negatives, with related pairs sharing source passages. Labels are synthetic, without independent adjudication or representative real-world distribution.

19. **How are precision, recall, and F1 calculated?**

    The evaluator creates unique unordered document pairs. Precision is TP/(TP+FP), recall is TP/(TP+FN), and F1 is their harmonic mean. It evaluates document-pair detection, not each chunk or a misconduct decision.

20. **Does the program detect AI-written text?**

    No reliable detection claim. It emits a clearly caveated style heuristic based on sentence-length variation, vocabulary diversity, and repeated bigrams.

21. **What does the external checker search?**

    Only the local JSON reference corpus. The supplied corpus is synthetic and does not represent internet search or comprehensive plagiarism coverage.

22. **How do failures affect a batch?**

    Each extractor catches per-file exceptions and returns an error/warning record. The CLI finishes with exit 0 if the pipeline completed; fatal pipeline-level errors return 1.

23. **What happens if MiniLM is unavailable?**

    `Embedder` records the exception and uses TF-IDF vectors. JSON and Markdown identify the score as lexical-only, and processing metadata includes the backend and model-loading error.

24. **What would you change to scale to 10,000 documents?**

    The README proposes queues, workers, PostgreSQL metadata, object storage, and Qdrant/Milvus HNSW. Those are architecture recommendations only. The prototype still computes an exact dense score matrix with quadratic memory, so larger deployments need candidate retrieval and batching.

25. **Would you use it to decide an academic case?**

    No. I would use it only to help a reviewer locate passages, then verify original files, context, citations, and assignment rules. It cannot establish intent, misconduct, or AI authorship.

## 10 difficult follow-up questions

1. **Your reported F1 is 1.00. Why should anyone trust it?**

   Trust only the metric arithmetic on these examples. There is a separate hold-out, but it has only ten candidate pairs, so it does not establish external validity. Broader independently authored and adjudicated examples are needed before making a performance claim.

2. **Did you tune the threshold on the evaluation data?**

   The 0.60 threshold was historically informed by the original synthetic development scores. It was not tuned on the separately authored hold-out. Development metrics remain in-sample; hold-out results are still a tiny synthetic regression check.

3. **How can you call a passage semantic when lexical overlap is only 0.07?**

   MiniLM returns 0.780 cosine for the paraphrase, which is why it crosses the weighted threshold. The result is plausible but needs independent human-labeled examples to validate that threshold and interpretation.

4. **Is this really multimodal?**

   Only in the input-source sense. For matching, MP4 speech is converted to text and compared with document text. It does not embed video frames or audio waveforms jointly.

5. **What role does `NumpyIndex` play?**

   The pipeline stores normalized vectors and chunk items in the exact NumPy index and uses its vectorized matrix multiplication for cosine scores. The dense matrix is practical for this small corpus but grows quadratically; HNSW-backed vector storage is a future scaling option.

6. **What if the same filename appears in two subdirectories?**

   Duplicate case-insensitive stems receive sanitized relative-path IDs with a SHA-256 suffix. Regression tests verify distinct reports and source links.

7. **What if MiniLM fails—are your match scores still semantic?**

   No. The fallback is TF-IDF-only, and JSON and Markdown label it lexical-only. It can detect word overlap but should not be presented as semantic paraphrase detection.

8. **How do you know external-reference matching works?**

   A regression test runs a matching synthetic passage and unrelated negative control through the pipeline and verifies the reference ID, excerpt, and title. This verifies the local JSON corpus path, not broad reference coverage.

9. **Could the reports leak student work?**

   Reports contain excerpts, so default generated report directories are ignored by Git. Keep real input and reports private and apply access/retention controls; ignore rules cannot identify sensitive files stored under arbitrary names.

10. **What security/performance risks remain for untrusted files?**

    FFmpeg/document extraction has no timeouts or size limits, and the all-pairs matrix is quadratic. Before processing untrusted or large batches I would add input/resource limits, subprocess timeouts, format validation, and a retrieval architecture.

## Limitations to state openly

- Perfect reported metrics are on 14 development and 5 hold-out synthetic submissions, not real coursework.
- The development threshold was informed by development examples; it was not tuned on hold-out data.
- Speech recognition can alter words; users must review audio for exact wording.
- Scanned PDFs have no OCR path.
- External matching is local-only; a positive synthetic reference regression is tested, but corpus coverage remains limited.
- The AI-writing signal is an uncalibrated heuristic and cannot identify authorship.
- The current system is in-memory and quadratic; the 10,000-document design is a proposal.
- The prototype remains quadratic in chunk count and lacks OCR and robust resource/time limits for untrusted inputs.
