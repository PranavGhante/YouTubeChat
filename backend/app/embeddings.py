import hashlib
import math
import os
import re
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[2] / ".env")


GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
GEMINI_EMBEDDING_DIMENSIONS = int(os.getenv("GEMINI_EMBEDDING_DIMENSIONS", "768"))


class HashEmbeddingFunction:
    def __init__(self, dimensions: int = 384):
        self.dimensions = dimensions

    def __call__(self, input: list[str]) -> list[list[float]]:
        return [self.embed_text(text) for text in input]

    def name(self) -> str:
        return "local-hash-embedding"

    def embed_query(self, input: list[str]) -> list[list[float]]:
        return self(input)

    def embed_documents(self, input: list[str]) -> list[list[float]]:
        return self(input)

    def embed_text(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        length = math.sqrt(sum(value * value for value in vector))
        if not length:
            return vector

        return [value / length for value in vector]


class GeminiEmbeddingFunction:
    def __init__(
        self,
        model: str = GEMINI_EMBEDDING_MODEL,
        dimensions: int = GEMINI_EMBEDDING_DIMENSIONS,
    ):
        from google import genai

        self.model = model
        self.dimensions = dimensions
        self.client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    def __call__(self, input: list[str]) -> list[list[float]]:
        return self.embed_documents(input)

    def name(self) -> str:
        return f"gemini-{self.model}-{self.dimensions}"

    def embed_query(self, input: list[str]) -> list[list[float]]:
        return self._embed(input, task_type="RETRIEVAL_QUERY")

    def embed_documents(self, input: list[str]) -> list[list[float]]:
        return self._embed(input, task_type="RETRIEVAL_DOCUMENT")

    def _embed(self, texts: list[str], task_type: str) -> list[list[float]]:
        from google.genai import types

        if not texts:
            return []

        result = self.client.models.embed_content(
            model=self.model,
            contents=texts,
            config=types.EmbedContentConfig(
                task_type=task_type,
                output_dimensionality=self.dimensions,
            ),
        )

        return [self._normalize(embedding.values) for embedding in result.embeddings]

    def _normalize(self, values: list[float]) -> list[float]:
        length = math.sqrt(sum(value * value for value in values))
        if not length:
            return list(values)

        return [value / length for value in values]


def create_embedding_function():
    if os.getenv("GEMINI_API_KEY"):
        return GeminiEmbeddingFunction()

    return HashEmbeddingFunction()
