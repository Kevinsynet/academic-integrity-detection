from src.chunker import chunk_document


def test_chunk_metadata_and_overlap():
    d = {
        "document_id": "d",
        "filename": "x.pdf",
        "source_segments": [{"text": " ".join(f"w{i}" for i in range(50)), "page": 4}],
    }
    c = chunk_document(d, 20, 5)
    assert len(c) > 1 and c[0]["metadata"]["page"] == 4 and c[0]["document_id"] == "d"
    assert c[0]["chunk_id"] == "d:0" and c[0]["metadata"]["filename"] == "x.pdf"
    assert c[0]["text"].split()[-5:] == c[1]["text"].split()[:5]


def test_default_chunk_configuration_is_in_assignment_range():
    from src.config import Config

    config = Config()
    assert 200 <= config.chunk_size <= 400
    assert 0 < config.overlap < config.chunk_size


def test_adjacent_whisper_segments_merge_and_keep_time_bounds():
    d = {
        "document_id": "v",
        "filename": "v.mp4",
        "source_segments": [
            {"text": "first spoken phrase", "start": 0.0, "end": 2.1},
            {"text": "second spoken phrase", "start": 2.1, "end": 4.7},
        ],
    }
    chunks = chunk_document(d, 50, 5)
    assert len(chunks) == 1
    assert chunks[0]["text"] == "first spoken phrase second spoken phrase"
    assert chunks[0]["metadata"]["start"] == 0.0 and chunks[0]["metadata"]["end"] == 4.7
    assert chunks[0]["metadata"]["source_segment_indices"] == [0, 1]
