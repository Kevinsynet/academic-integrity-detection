# Integrity review: holdout_exact_copy

**Risk classification:** HIGH

**Original submission:** [holdout_exact_copy.pdf](../holdout_submissions/pdf/holdout_exact_copy.pdf)

## Signal breakdown

- Peer similarity: 100.0%
- External similarity: 0.0%
- AI heuristic indicator: 28.1%

## Embedding and comparison

- Backend: sentence-transformers/all-MiniLM-L6-v2
- Score method: combined_minilm_tfidf
- Rule: 0.8 * MiniLM semantic cosine + 0.2 * TF-IDF lexical cosine
- Threshold: 0.6

- Risk bands: MEDIUM at 10.0% coverage; HIGH at 25.0% coverage

## Matches

### Peer Matches
- **holdout_original** (combined 1.000; MiniLM semantic cosine 1.000; lexical cosine 1.000; page 1 ↔ page 1; source submission: [holdout_original.pdf](../holdout_submissions/pdf/holdout_original.pdf))
  - Query: “The fictional city of Norvale installed reflective roof panels at three public libraries. Over one summer, researchers measured indoor temperatures every afternoon and compared the readings with nearby buildings without panels. The libraries stayed cooler during heat waves, while shaded reading rooms remained open to residents who lacked air conditioning.”
  - Source: “The fictional city of Norvale installed reflective roof panels at three public libraries. Over one summer, researchers measured indoor temperatures every afternoon and compared the readings with nearby buildings without panels. The libraries stayed cooler during heat waves, while shaded reading rooms remained open to residents who lacked air conditioning.”
  - The semantic embedding cosine is 1.000, lexical cosine is 1.000, and the 0.8/0.2 combined score is 1.000; verify the displayed excerpts and locations.
- **holdout_spoken** (combined 0.924; MiniLM semantic cosine 0.942; lexical cosine 0.851; page 1 ↔ 0.0–19.0s; source submission: [holdout_spoken.mp4](../holdout_submissions/video/holdout_spoken.mp4))
  - Query: “The fictional city of Norvale installed reflective roof panels at three public libraries. Over one summer, researchers measured indoor temperatures every afternoon and compared the readings with nearby buildings without panels. The libraries stayed cooler during heat waves, while shaded reading rooms remained open to residents who lacked air conditioning.”
  - Source: “The fictional city of Norval installed reflective roof panels at three public libraries. Over one summer, researchers measured indoor temperatures every afternoon and compared the readings with nearby buildings without panels. The library stayed cooler during heat waves, while shaded reading rooms remained open to residents who lacked error conditioning.”
  - The semantic embedding cosine is 0.942, lexical cosine is 0.851, and the 0.8/0.2 combined score is 0.924; verify the displayed excerpts and locations.
- **holdout_paraphrase** (combined 0.719; MiniLM semantic cosine 0.868; lexical cosine 0.119; page 1 ↔ paragraph 2; source submission: [holdout_paraphrase.docx](../holdout_submissions/docx/holdout_paraphrase.docx))
  - Query: “The fictional city of Norvale installed reflective roof panels at three public libraries. Over one summer, researchers measured indoor temperatures every afternoon and compared the readings with nearby buildings without panels. The libraries stayed cooler during heat waves, while shaded reading rooms remained open to residents who lacked air conditioning.”
  - Source: “Three Norvale libraries received bright roof coatings in a made-up city experiment. Investigators recorded room heat each afternoon through the summer and used neighboring untreated buildings for comparison. During hot spells, the treated libraries had lower temperatures, and their shaded spaces offered a refuge for people whose homes had no cooling system.”
  - The semantic embedding cosine is 0.868, lexical cosine is 0.119, and the 0.8/0.2 combined score is 0.718; verify the displayed excerpts and locations.

### Multimodal Matches
- **holdout_spoken** (combined 0.924; MiniLM semantic cosine 0.942; lexical cosine 0.851; page 1 ↔ 0.0–19.0s; source submission: [holdout_spoken.mp4](../holdout_submissions/video/holdout_spoken.mp4))
  - Query: “The fictional city of Norvale installed reflective roof panels at three public libraries. Over one summer, researchers measured indoor temperatures every afternoon and compared the readings with nearby buildings without panels. The libraries stayed cooler during heat waves, while shaded reading rooms remained open to residents who lacked air conditioning.”
  - Source: “The fictional city of Norval installed reflective roof panels at three public libraries. Over one summer, researchers measured indoor temperatures every afternoon and compared the readings with nearby buildings without panels. The library stayed cooler during heat waves, while shaded reading rooms remained open to residents who lacked error conditioning.”
  - The semantic embedding cosine is 0.942, lexical cosine is 0.851, and the 0.8/0.2 combined score is 0.924; verify the displayed excerpts and locations.

### External Matches
- No significant matches detected.

## AI analysis limitations

Heuristic pattern score only; writing style cannot establish authorship and human text may score highly.

## Warnings

- None recorded.