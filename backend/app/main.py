from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from youtube_transcript_api import (
    NoTranscriptFound,
    TranscriptsDisabled,
    YouTubeTranscriptApi,
)

from .chunking import chunk_transcript
from .schemas import (
    ChatRequest,
    ChatResponse,
    IndexVideoResponse,
    SearchRequest,
    SearchResponse,
    TranscriptEntry,
    TranscriptRequest,
    TranscriptResponse,
)
from .llm import (
    answer_with_citations,
    get_or_create_conversation_id,
    rewrite_query,
    save_turn,
)
from .vector_store import search_chunks, store_chunks
from .youtube import InvalidYouTubeUrlError, extract_video_id, format_timestamp


app = FastAPI(title="YouTube Transcript API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/transcript", response_model=TranscriptResponse)
def get_transcript(payload: TranscriptRequest) -> TranscriptResponse:
    video_id, transcript = fetch_transcript(payload.url)
    return TranscriptResponse(video_id=video_id, transcript=transcript)


@app.post("/api/index", response_model=IndexVideoResponse)
def index_video(payload: TranscriptRequest) -> IndexVideoResponse:
    video_id, transcript = fetch_transcript(payload.url)
    chunks = chunk_transcript(video_id, transcript)
    store_chunks(video_id, chunks)

    return IndexVideoResponse(
        video_id=video_id,
        transcript_count=len(transcript),
        chunk_count=len(chunks),
        chunks=chunks,
    )


@app.post("/api/search", response_model=SearchResponse)
def search_video(payload: SearchRequest) -> SearchResponse:
    try:
        results = search_chunks(payload.video_id, payload.query, payload.limit)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Could not search indexed chunks.",
        ) from exc

    return SearchResponse(
        video_id=payload.video_id,
        query=payload.query,
        results=results,
    )


@app.post("/api/chat", response_model=ChatResponse)
def chat_video(payload: ChatRequest) -> ChatResponse:
    conversation_id = get_or_create_conversation_id(payload.conversation_id)
    rewritten_query = rewrite_query(conversation_id, payload.message)
    try:
        results = search_chunks(payload.video_id, rewritten_query, payload.limit)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Could not retrieve transcript chunks for this question.",
        ) from exc

    try:
        answer, citations = answer_with_citations(
            question=payload.message,
            rewritten_query=rewritten_query,
            results=results,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Could not generate an answer from the retrieved chunks.",
        ) from exc

    save_turn(conversation_id, payload.message, answer)

    return ChatResponse(
        conversation_id=conversation_id,
        video_id=payload.video_id,
        message=payload.message,
        rewritten_query=rewritten_query,
        answer=answer,
        citations=citations,
    )


def fetch_transcript(url: str) -> tuple[str, list[TranscriptEntry]]:
    try:
        video_id = extract_video_id(url)
    except InvalidYouTubeUrlError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        raw_transcript = YouTubeTranscriptApi().fetch(video_id)
    except TranscriptsDisabled as exc:
        raise HTTPException(
            status_code=404,
            detail="Transcripts are disabled for this video.",
        ) from exc
    except NoTranscriptFound as exc:
        raise HTTPException(
            status_code=404,
            detail="No transcript was found for this video.",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Could not fetch the transcript for this video.",
        ) from exc

    transcript = [normalize_transcript_entry(entry) for entry in raw_transcript]
    return video_id, transcript


def normalize_transcript_entry(entry: Any) -> TranscriptEntry:
    start = float(getattr(entry, "start"))
    duration = float(getattr(entry, "duration"))
    end = start + duration

    return TranscriptEntry(
        text=str(getattr(entry, "text")).strip(),
        start=start,
        duration=duration,
        end=end,
        timestamp=format_timestamp(start),
    )
