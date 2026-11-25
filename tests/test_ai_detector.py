from src.ai_detector import analyze_ai


def test_ai_indicator_has_required_fields_and_is_documented_as_heuristic():
    text = (
        "The coordinated initiative demonstrates a multifaceted approach to community resilience. "
        "Furthermore, the framework enables stakeholders to leverage shared responsibilities. "
        "Consequently, these measurable outcomes support broader community wellbeing. "
        "The findings underscore the importance of continued collaboration."
    )
    result = analyze_ai(text)
    assert 0.0 <= result["ai_generated_probability"] <= 1.0
    assert {"sentence_length_cv", "type_token_ratio", "repeated_bigram_rate"} <= result[
        "features_used"
    ].keys()
    assert "uncalibrated" in result["detector_method"]
    assert "cannot establish authorship" in result["explanation"]
