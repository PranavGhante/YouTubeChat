from pathlib import Path
from typing import Any

import chromadb

from .embeddings import create_embedding_function
from .schemas import ChunkEntry, SearchResult


CHROMA_DIR = Path(__file__).resolve().parents[1] / "chroma"


embedding_function = create_embedding_function()
COLLECTION_NAME = f"youtube_transcript_chunks_{embedding_function.name()}".replace(
    "-",
    "_",
)
client = chromadb.PersistentClient(path=str(CHROMA_DIR))
collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=embedding_function,
    metadata={"hnsw:space": "cosine"},
)


def store_chunks(video_id: str, chunks: list[ChunkEntry]) -> None:
    if not chunks:
        return

    existing = collection.get(where={"video_id": video_id})
    existing_ids = existing.get("ids", [])
    if existing_ids:
        collection.delete(ids=existing_ids)

    collection.add(
        ids=[chunk.id for chunk in chunks],
        documents=[chunk.text for chunk in chunks],
        metadatas=[_chunk_metadata(chunk) for chunk in chunks],
    )


def search_chunks(video_id: str, query: str, limit: int) -> list[SearchResult]:
    result = collection.query(
        query_texts=[query],
        n_results=limit,
        where={"video_id": video_id},
    )

    ids = result.get("ids", [[]])[0]
    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]

    search_results: list[SearchResult] = []
    for index, chunk_id in enumerate(ids):
        metadata = metadatas[index]
        search_results.append(
            SearchResult(
                id=chunk_id,
                video_id=str(metadata["video_id"]),
                text=documents[index],
                start=float(metadata["start"]),
                end=float(metadata["end"]),
                start_timestamp=str(metadata["start_timestamp"]),
                end_timestamp=str(metadata["end_timestamp"]),
                chunk_index=int(metadata["chunk_index"]),
                distance=float(distances[index]) if distances else None,
            )
        )

    return search_results


def _chunk_metadata(chunk: ChunkEntry) -> dict[str, Any]:
    return {
        "video_id": chunk.video_id,
        "start": chunk.start,
        "end": chunk.end,
        "start_timestamp": chunk.start_timestamp,
        "end_timestamp": chunk.end_timestamp,
        "chunk_index": chunk.chunk_index,
    }
