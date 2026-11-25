# Integrity review: original_river

**Risk classification:** HIGH

**Original submission:** [original_river.docx](../sample_submissions/docx/original_river.docx)

## Signal breakdown

- Peer similarity: 100.0%
- External similarity: 0.0%
- AI heuristic indicator: 15.1%

## Embedding and comparison

- Backend: sentence-transformers/all-MiniLM-L6-v2
- Score method: combined_minilm_tfidf
- Rule: 0.8 * MiniLM semantic cosine + 0.2 * TF-IDF lexical cosine
- Threshold: 0.6

- Risk bands: MEDIUM at 10.0% coverage; HIGH at 25.0% coverage

## Matches

### Peer Matches
- **original_river_spoken** (combined 0.883; MiniLM semantic cosine 0.955; lexical cosine 0.594; paragraph 3 ↔ 0.0–17.6s; source submission: [original_river_spoken.mp4](../sample_submissions/video/original_river_spoken.mp4))
  - Query: “A fictional river monitoring group found that placing sampling kits near bus stops increased volunteer participation. The team compared weekly signups and found transport access mattered more than reminder frequency.”
  - Source: “A fictional river monitor in group found that placing sampling kits near bus stops increased volunteer participation, the team compared weekly sign-ups and found transport access mattered more than reminder frequency, they repeated observations across seasonal surveys and shared the results with the local watershed council.”
  - The semantic embedding cosine is 0.955, lexical cosine is 0.594, and the 0.8/0.2 combined score is 0.883; verify the displayed excerpts and locations.

### Multimodal Matches
- **original_river_spoken** (combined 0.883; MiniLM semantic cosine 0.955; lexical cosine 0.594; paragraph 3 ↔ 0.0–17.6s; source submission: [original_river_spoken.mp4](../sample_submissions/video/original_river_spoken.mp4))
  - Query: “A fictional river monitoring group found that placing sampling kits near bus stops increased volunteer participation. The team compared weekly signups and found transport access mattered more than reminder frequency.”
  - Source: “A fictional river monitor in group found that placing sampling kits near bus stops increased volunteer participation, the team compared weekly sign-ups and found transport access mattered more than reminder frequency, they repeated observations across seasonal surveys and shared the results with the local watershed council.”
  - The semantic embedding cosine is 0.955, lexical cosine is 0.594, and the 0.8/0.2 combined score is 0.883; verify the displayed excerpts and locations.

### External Matches
- No significant matches detected.

## AI analysis limitations

Heuristic pattern score only; writing style cannot establish authorship and human text may score highly.

## Warnings

- None recorded.