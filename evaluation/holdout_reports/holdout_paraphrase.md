# Integrity review: holdout_paraphrase

**Risk classification:** HIGH

**Original submission:** [holdout_paraphrase.docx](../holdout_submissions/docx/holdout_paraphrase.docx)

## Signal breakdown

- Peer similarity: 100.0%
- External similarity: 0.0%
- AI heuristic indicator: 26.1%

## Embedding and comparison

- Backend: sentence-transformers/all-MiniLM-L6-v2
- Score method: combined_minilm_tfidf
- Rule: 0.8 * MiniLM semantic cosine + 0.2 * TF-IDF lexical cosine
- Threshold: 0.6

- Risk bands: MEDIUM at 10.0% coverage; HIGH at 25.0% coverage

## Matches

### Peer Matches
- **holdout_exact_copy** (combined 0.719; MiniLM semantic cosine 0.868; lexical cosine 0.119; paragraph 2 ↔ page 1; source submission: [holdout_exact_copy.pdf](../holdout_submissions/pdf/holdout_exact_copy.pdf))
  - Query: “Three Norvale libraries received bright roof coatings in a made-up city experiment. Investigators recorded room heat each afternoon through the summer and used neighboring untreated buildings for comparison. During hot spells, the treated libraries had lower temperatures, and their shaded spaces offered a refuge for people whose homes had no cooling system.”
  - Source: “The fictional city of Norvale installed reflective roof panels at three public libraries. Over one summer, researchers measured indoor temperatures every afternoon and compared the readings with nearby buildings without panels. The libraries stayed cooler during heat waves, while shaded reading rooms remained open to residents who lacked air conditioning.”
  - The semantic embedding cosine is 0.868, lexical cosine is 0.119, and the 0.8/0.2 combined score is 0.718; verify the displayed excerpts and locations.
- **holdout_original** (combined 0.719; MiniLM semantic cosine 0.868; lexical cosine 0.119; paragraph 2 ↔ page 1; source submission: [holdout_original.pdf](../holdout_submissions/pdf/holdout_original.pdf))
  - Query: “Three Norvale libraries received bright roof coatings in a made-up city experiment. Investigators recorded room heat each afternoon through the summer and used neighboring untreated buildings for comparison. During hot spells, the treated libraries had lower temperatures, and their shaded spaces offered a refuge for people whose homes had no cooling system.”
  - Source: “The fictional city of Norvale installed reflective roof panels at three public libraries. Over one summer, researchers measured indoor temperatures every afternoon and compared the readings with nearby buildings without panels. The libraries stayed cooler during heat waves, while shaded reading rooms remained open to residents who lacked air conditioning.”
  - The semantic embedding cosine is 0.868, lexical cosine is 0.119, and the 0.8/0.2 combined score is 0.718; verify the displayed excerpts and locations.
- **holdout_spoken** (combined 0.683; MiniLM semantic cosine 0.828; lexical cosine 0.103; paragraph 2 ↔ 0.0–19.0s; source submission: [holdout_spoken.mp4](../holdout_submissions/video/holdout_spoken.mp4))
  - Query: “Three Norvale libraries received bright roof coatings in a made-up city experiment. Investigators recorded room heat each afternoon through the summer and used neighboring untreated buildings for comparison. During hot spells, the treated libraries had lower temperatures, and their shaded spaces offered a refuge for people whose homes had no cooling system.”
  - Source: “The fictional city of Norval installed reflective roof panels at three public libraries. Over one summer, researchers measured indoor temperatures every afternoon and compared the readings with nearby buildings without panels. The library stayed cooler during heat waves, while shaded reading rooms remained open to residents who lacked error conditioning.”
  - The semantic embedding cosine is 0.828, lexical cosine is 0.103, and the 0.8/0.2 combined score is 0.683; verify the displayed excerpts and locations.

### Multimodal Matches
- **holdout_spoken** (combined 0.683; MiniLM semantic cosine 0.828; lexical cosine 0.103; paragraph 2 ↔ 0.0–19.0s; source submission: [holdout_spoken.mp4](../holdout_submissions/video/holdout_spoken.mp4))
  - Query: “Three Norvale libraries received bright roof coatings in a made-up city experiment. Investigators recorded room heat each afternoon through the summer and used neighboring untreated buildings for comparison. During hot spells, the treated libraries had lower temperatures, and their shaded spaces offered a refuge for people whose homes had no cooling system.”
  - Source: “The fictional city of Norval installed reflective roof panels at three public libraries. Over one summer, researchers measured indoor temperatures every afternoon and compared the readings with nearby buildings without panels. The library stayed cooler during heat waves, while shaded reading rooms remained open to residents who lacked error conditioning.”
  - The semantic embedding cosine is 0.828, lexical cosine is 0.103, and the 0.8/0.2 combined score is 0.683; verify the displayed excerpts and locations.

### External Matches
- No significant matches detected.

## AI analysis limitations

Heuristic pattern score only; writing style cannot establish authorship and human text may score highly.

## Warnings

- None recorded.