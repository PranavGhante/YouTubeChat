from pydantic import BaseModel, Field


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


class ChunkEntry(BaseModel):
    id: str
    video_id: str
    text: str
    start: float
    end: float
    start_timestamp: str
    end_timestamp: str
    chunk_index: int


class IndexVideoResponse(BaseModel):
    video_id: str
    transcript_count: int
    chunk_count: int
    chunks: list[ChunkEntry]


class SearchRequest(BaseModel):
    video_id: str = Field(..., min_length=1)
    query: str = Field(..., min_length=1)
    limit: int = Field(default=5, ge=1, le=20)


class SearchResult(BaseModel):
    id: str
    video_id: str
    text: str
    start: float
    end: float
    start_timestamp: str
    end_timestamp: str
    chunk_index: int
    distance: float | None = None


class SearchResponse(BaseModel):
    video_id: str
    query: str
    results: list[SearchResult]


class ChatTurn(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    video_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    conversation_id: str | None = None
    limit: int = Field(default=6, ge=1, le=12)


class Citation(BaseModel):
    id: str
    text: str
    start: float
    end: float
    start_timestamp: str
    end_timestamp: str
    chunk_index: int


class ChatResponse(BaseModel):
    conversation_id: str
    video_id: str
    message: str
    rewritten_query: str
    answer: str
    citations: list[Citation]
