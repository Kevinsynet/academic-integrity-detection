"""Transparent, uncalibrated writing-style heuristic for reviewer context."""

import re


def analyze_ai(text):
    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", text)
        if sentence.strip()
    ]
    words = re.findall(r"[\w']+", text.lower())
    word_count = len(words)
    if word_count < 20:
        return {
            "ai_generated_probability": 0.0,
            "features_used": {},
            "explanation": "Insufficient text for a stable heuristic estimate.",
            "detector_method": "transparent linguistic heuristic; not calibrated",
        }

    sentence_lengths = [len(re.findall(r"\w+", sentence)) for sentence in sentences] or [0]
    vocabulary_ratio = len(set(words)) / max(word_count, 1)
    bigrams = list(zip(words, words[1:]))
    repeated_bigram_rate = 1 - len(set(bigrams)) / max(1, word_count - 1)
    mean_length = sum(sentence_lengths) / len(sentence_lengths)
    variance = sum((length - mean_length) ** 2 for length in sentence_lengths) / len(sentence_lengths)
    standard_deviation = variance ** 0.5
    length_cv = standard_deviation / max(mean_length, 1)
    smoothness = 1 - min(1, length_cv)
    score = max(
        0,
        min(1, 0.30 * smoothness + 0.35 * (1 - vocabulary_ratio)
            + 0.35 * min(1, repeated_bigram_rate * 4)),
    )
    return {
        "ai_generated_probability": round(score, 4),
        "features_used": {
            "sentence_length_cv": round(length_cv, 4),
            "type_token_ratio": round(vocabulary_ratio, 4),
            "repeated_bigram_rate": round(repeated_bigram_rate, 4),
        },
        "explanation": (
            "Heuristic pattern score only; writing style cannot establish authorship and "
            "human text may score highly."
        ),
        "detector_method": (
            "reproducible length-variation, vocabulary-diversity, and "
            "repeated-bigram heuristic; uncalibrated"
        ),
    }
