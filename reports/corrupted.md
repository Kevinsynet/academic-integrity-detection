# Integrity review: corrupted

**Risk classification:** LOW

**Original submission:** [corrupted.pdf](../sample_submissions/pdf/corrupted.pdf)

## Signal breakdown

- Peer similarity: 0.0%
- External similarity: 0.0%
- AI heuristic indicator: 0.0%

## Embedding and comparison

- Backend: sentence-transformers/all-MiniLM-L6-v2
- Score method: combined_minilm_tfidf
- Rule: 0.8 * MiniLM semantic cosine + 0.2 * TF-IDF lexical cosine
- Threshold: 0.6

- Risk bands: MEDIUM at 10.0% coverage; HIGH at 25.0% coverage

## Matches

### Peer Matches
- No significant matches detected.

### Multimodal Matches
- No significant matches detected.

### External Matches
- No significant matches detected.

## AI analysis limitations

Insufficient text for a stable heuristic estimate.

## Warnings

- Extraction failed: FileDataError: Failed to open file 'sample_submissions/pdf/corrupted.pdf' as type pdf.