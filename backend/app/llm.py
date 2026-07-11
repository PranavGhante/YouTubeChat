import os
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from google import genai
from google.genai import types

from .schemas import ChatTurn, Citation, SearchResult


load_dotenv(Path(__file__).resolve().parents[2] / ".env")

LLM_MODEL = os.getenv("LLM_MODEL", "gemini-flash-lite-latest")
MAX_HISTORY_TURNS = 8

conversations: dict[str, list[ChatTurn]] = {}


def get_or_create_conversation_id(conversation_id: str | None) -> str:
    if conversation_id:
        conversations.setdefault(conversation_id, [])
        return conversation_id

    new_id = str(uuid4())
    conversations[new_id] = []
    return new_id


def rewrite_query(conversation_id: str, message: str) -> str:
    history = conversations.get(conversation_id, [])
    if not history:
        return message

    prompt = (
        "Rewrite the latest user message as a standalone search query for a "
        "YouTube transcript RAG system. Preserve names, topics, and time "
        "references. Return only the rewritten query.\n\n"
        f"Recent conversation:\n{_format_history(history[-MAX_HISTORY_TURNS:])}\n\n"
        f"Latest user message: {message}"
    )

    return _generate_text(prompt).strip() or message


def answer_with_citations(
    question: str,
    rewritten_query: str,
    results: list[SearchResult],
) -> tuple[str, list[Citation]]:
    if not results:
        return (
            "I could not find relevant transcript chunks for that question.",
            [],
        )

    context = "\n\n".join(
        (
            f"[{index + 1}] Time: {result.start_timestamp}-"
            f"{result.end_timestamp}\n{result.text}"
        )
        for index, result in enumerate(results)
    )
    prompt = (
        "You answer questions about a YouTube video using only the transcript "
        "chunks below. If the answer is not supported by the chunks, say you "
        "could not find it in the indexed transcript. Cite every factual claim "
        "with chunk numbers like [1] or [2]. Do not mention chunks that are not "
        "needed.\n\n"
        f"User question: {question}\n"
        f"Search query used: {rewritten_query}\n\n"
        f"Transcript chunks:\n{context}\n\n"
        "Answer:"
    )

    answer = _generate_text(prompt).strip()
    citations = []
    for index, result in enumerate(results):
        if f"[{index + 1}]" in answer:
            citations.append(_result_to_citation(result))

    if not citations:
        citations = [_result_to_citation(result) for result in results[:3]]

    return answer, citations


def save_turn(conversation_id: str, user_message: str, assistant_answer: str) -> None:
    history = conversations.setdefault(conversation_id, [])
    history.extend(
        [
            ChatTurn(role="user", content=user_message),
            ChatTurn(role="assistant", content=assistant_answer),
        ]
    )
    conversations[conversation_id] = history[-MAX_HISTORY_TURNS:]


def _generate_text(prompt: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is required for chat answers.")

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=LLM_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2,
        ),
    )

    return response.text or ""


def _result_to_citation(result: SearchResult) -> Citation:
    return Citation(
        id=result.id,
        text=result.text,
        start=result.start,
        end=result.end,
        start_timestamp=result.start_timestamp,
        end_timestamp=result.end_timestamp,
        chunk_index=result.chunk_index,
    )


def _format_history(history: list[ChatTurn]) -> str:
    return "\n".join(f"{turn.role}: {turn.content}" for turn in history)
