"""Location-preserving chunking, including merged Whisper segments."""

from .normalizer import normalize_text


def chunk_document(document, chunk_size=300, overlap=45):
    chunks = []
    step = max(1, chunk_size - overlap)
    timed_words = []

    def append_chunk(words, metadata):
        if not words:
            return
        chunks.append({
            "chunk_id": f"{document['document_id']}:{len(chunks)}",
            "document_id": document["document_id"],
            "text": " ".join(words),
            "metadata": metadata,
        })

    for segment_index, segment in enumerate(document.get("source_segments", [])):
        words = normalize_text(segment.get("text", "")).split()
        if not words:
            continue
        if "start" in segment and "end" in segment:
            for word in words:
                timed_words.append((word, float(segment["start"]), float(segment["end"]), segment_index))
            continue

        for start_index in range(0, len(words), step):
            part = words[start_index:start_index + chunk_size]
            metadata = {key: value for key, value in segment.items() if key != "text"}
            metadata.update({"filename": document["filename"], "segment_index": segment_index})
            append_chunk(part, metadata)
            if start_index + chunk_size >= len(words):
                break

    # Whisper output is sentence/phrase segmented. Reassemble it before text chunking so
    # short adjacent transcript fragments can be compared with a complete page passage.
    for start_index in range(0, len(timed_words), step):
        part = timed_words[start_index:start_index + chunk_size]
        if not part:
            continue
        source_indices = list(dict.fromkeys(item[3] for item in part))
        metadata = {
            "filename": document["filename"],
            "start": part[0][1],
            "end": part[-1][2],
            "source_segment_indices": source_indices,
        }
        append_chunk([item[0] for item in part], metadata)
        if start_index + chunk_size >= len(timed_words):
            break
    return chunks
