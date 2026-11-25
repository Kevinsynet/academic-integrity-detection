# Integrity review: coastal_paraphrase

**Risk classification:** HIGH

**Original submission:** [coastal_paraphrase.pdf](../sample_submissions/pdf/coastal_paraphrase.pdf)

## Signal breakdown

- Peer similarity: 100.0%
- External similarity: 0.0%
- AI heuristic indicator: 28.5%

## Embedding and comparison

- Backend: sentence-transformers/all-MiniLM-L6-v2
- Score method: combined_minilm_tfidf
- Rule: 0.8 * MiniLM semantic cosine + 0.2 * TF-IDF lexical cosine
- Threshold: 0.6

- Risk bands: MEDIUM at 10.0% coverage; HIGH at 25.0% coverage

## Matches

### Peer Matches
- **garden_paraphrase** (combined 1.000; MiniLM semantic cosine 1.000; lexical cosine 1.000; page 1 ↔ paragraph 3; source submission: [garden_paraphrase.docx](../sample_submissions/docx/garden_paraphrase.docx))
  - Query: “In Alderwick, neighbors transformed vacant municipal land into a communal growing space. They rotated irrigation duties, recorded weekly moisture readings, and reviewed plot yields. A simple shared schedule spread the labor while extending produce access to people in flats.”
  - Source: “In Alderwick, neighbors transformed vacant municipal land into a communal growing space. They rotated irrigation duties, recorded weekly moisture readings, and reviewed plot yields. A simple shared schedule spread the labor while extending produce access to people in flats.”
  - The semantic embedding cosine is 1.000, lexical cosine is 1.000, and the 0.8/0.2 combined score is 1.000; verify the displayed excerpts and locations.
- **garden_copy** (combined 0.638; MiniLM semantic cosine 0.780; lexical cosine 0.071; page 1 ↔ page 1; source submission: [garden_copy.pdf](../sample_submissions/pdf/garden_copy.pdf))
  - Query: “In Alderwick, neighbors transformed vacant municipal land into a communal growing space. They rotated irrigation duties, recorded weekly moisture readings, and reviewed plot yields. A simple shared schedule spread the labor while extending produce access to people in flats.”
  - Source: “The fictional town of Alderwick converted an unused lot into a neighborhood garden. Residents formed watering teams, tracked soil moisture each week, and compared harvests. Shared rules helped distribute work and gave apartment residents access to fresh food.”
  - The semantic embedding cosine is 0.780, lexical cosine is 0.071, and the 0.8/0.2 combined score is 0.638; verify the displayed excerpts and locations.
- **garden_original** (combined 0.638; MiniLM semantic cosine 0.780; lexical cosine 0.071; page 1 ↔ page 1; source submission: [garden_original.pdf](../sample_submissions/pdf/garden_original.pdf))
  - Query: “In Alderwick, neighbors transformed vacant municipal land into a communal growing space. They rotated irrigation duties, recorded weekly moisture readings, and reviewed plot yields. A simple shared schedule spread the labor while extending produce access to people in flats.”
  - Source: “The fictional town of Alderwick converted an unused lot into a neighborhood garden. Residents formed watering teams, tracked soil moisture each week, and compared harvests. Shared rules helped distribute work and gave apartment residents access to fresh food.”
  - The semantic embedding cosine is 0.780, lexical cosine is 0.071, and the 0.8/0.2 combined score is 0.638; verify the displayed excerpts and locations.
- **garden_spoken** (combined 0.626; MiniLM semantic cosine 0.763; lexical cosine 0.078; page 1 ↔ 0.0–14.3s; source submission: [garden_spoken.mp4](../sample_submissions/video/garden_spoken.mp4))
  - Query: “In Alderwick, neighbors transformed vacant municipal land into a communal growing space. They rotated irrigation duties, recorded weekly moisture readings, and reviewed plot yields. A simple shared schedule spread the labor while extending produce access to people in flats.”
  - Source: “The fictional town of Alderwick converted and unused lot into a neighborhood garden, residents formed watering teams, track soil moisture each week, and compared harvests, shared rules helped distribute work and gave apartment residents access to fresh food.”
  - The semantic embedding cosine is 0.763, lexical cosine is 0.078, and the 0.8/0.2 combined score is 0.626; verify the displayed excerpts and locations.

### Multimodal Matches
- **garden_spoken** (combined 0.626; MiniLM semantic cosine 0.763; lexical cosine 0.078; page 1 ↔ 0.0–14.3s; source submission: [garden_spoken.mp4](../sample_submissions/video/garden_spoken.mp4))
  - Query: “In Alderwick, neighbors transformed vacant municipal land into a communal growing space. They rotated irrigation duties, recorded weekly moisture readings, and reviewed plot yields. A simple shared schedule spread the labor while extending produce access to people in flats.”
  - Source: “The fictional town of Alderwick converted and unused lot into a neighborhood garden, residents formed watering teams, track soil moisture each week, and compared harvests, shared rules helped distribute work and gave apartment residents access to fresh food.”
  - The semantic embedding cosine is 0.763, lexical cosine is 0.078, and the 0.8/0.2 combined score is 0.626; verify the displayed excerpts and locations.

### External Matches
- No significant matches detected.

## AI analysis limitations

Heuristic pattern score only; writing style cannot establish authorship and human text may score highly.

## Warnings

- None recorded.