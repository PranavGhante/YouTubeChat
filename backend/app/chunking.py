from .schemas import ChunkEntry, TranscriptEntry
from .youtube import format_timestamp


MAX_CHUNK_WORDS = 140
OVERLAP_WORDS = 30


def chunk_transcript(
    video_id: str,
    transcript: list[TranscriptEntry],
    max_words: int = MAX_CHUNK_WORDS,
    overlap_words: int = OVERLAP_WORDS,
) -> list[ChunkEntry]:
    chunks: list[ChunkEntry] = []
    current_entries: list[TranscriptEntry] = []
    current_word_count = 0

    for entry in transcript:
        words = entry.text.split()
        if not words:
            continue

        should_flush = current_entries and current_word_count + len(words) > max_words
        if should_flush:
            chunks.append(_build_chunk(video_id, len(chunks), current_entries))
            current_entries = _overlap_entries(current_entries, overlap_words)
            current_word_count = sum(len(item.text.split()) for item in current_entries)

        current_entries.append(entry)
        current_word_count += len(words)

    if current_entries:
        chunks.append(_build_chunk(video_id, len(chunks), current_entries))

    return chunks


def _build_chunk(
    video_id: str,
    chunk_index: int,
    entries: list[TranscriptEntry],
) -> ChunkEntry:
    start = entries[0].start
    end = entries[-1].end
    text = " ".join(entry.text for entry in entries).strip()

    return ChunkEntry(
        id=f"{video_id}:{chunk_index}",
        video_id=video_id,
        text=text,
        start=start,
        end=end,
        start_timestamp=format_timestamp(start),
        end_timestamp=format_timestamp(end),
        chunk_index=chunk_index,
    )


def _overlap_entries(
    entries: list[TranscriptEntry],
    overlap_words: int,
) -> list[TranscriptEntry]:
    if overlap_words <= 0:
        return []

    selected: list[TranscriptEntry] = []
    word_count = 0

    for entry in reversed(entries):
        selected.append(entry)
        word_count += len(entry.text.split())
        if word_count >= overlap_words:
            break

    selected.reverse()
    return selected
