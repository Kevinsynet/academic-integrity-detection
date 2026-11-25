from src.normalizer import remove_repeated_template_sentences


def test_repeated_template_removal_preserves_analysis_and_location():
    boiler = "This synthetic case study examines shared resources."
    docs = [
        {
            "extracted_text": "",
            "source_segments": [
                {
                    "text": boiler
                    + " Alderwick residents measured garden yields every week.",
                    "page": 1,
                }
            ],
        },
        {
            "extracted_text": "",
            "source_segments": [
                {
                    "text": boiler
                    + " A river group logged rainfall at three locations.",
                    "page": 2,
                }
            ],
        },
    ]
    removed = remove_repeated_template_sentences(docs, 0.5)
    assert boiler.lower() in removed
    assert boiler not in docs[0]["source_segments"][0]["text"]
    assert "Alderwick residents measured" in docs[0]["extracted_text"]
    assert docs[0]["source_segments"][0]["page"] == 1


def test_frequency_filter_removes_admin_boilerplate_but_preserves_repeated_analysis():
    from src.normalizer import remove_repeated_template_sentences

    boiler = "All submissions use the same review protocol and shared reporting format for this demonstration project; this standard administrative note contains no findings."
    analysis = "The field survey found that shaded plots retained more moisture during the unusually hot summer."
    docs = [
        {"extracted_text": "", "source_segments": [{"text": boiler + " " + analysis}]}
        for _ in range(4)
    ]
    removed = remove_repeated_template_sentences(docs, 0.5)
    assert boiler.lower() in removed
    assert analysis.lower() not in removed
    assert all(analysis in doc["extracted_text"] for doc in docs)
