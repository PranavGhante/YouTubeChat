from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from youtube_transcript_api import (
    NoTranscriptFound,
    TranscriptsDisabled,
    YouTubeTranscriptApi,
)

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


class TranscriptRequest(BaseModel):
    url: str = Field(..., min_length=1)


class TranscriptEntry(BaseModel):
    text: str
    start: float
    duration: float
    end: float
    timestamp: str


class TranscriptResponse(BaseModel):
    video_id: str
    transcript: list[TranscriptEntry]


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/transcript", response_model=TranscriptResponse)
def get_transcript(payload: TranscriptRequest) -> TranscriptResponse:
    try:
        video_id = extract_video_id(payload.url)
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
    return TranscriptResponse(video_id=video_id, transcript=transcript)


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
