from functools import lru_cache

from google import genai
from google.genai import types

from app.core.config import settings


@lru_cache
def get_gemini_client():
    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    retry_options = types.HttpRetryOptions(
        attempts=2,
        initial_delay=1.0,
        max_delay=2.0,
        exp_base=2.0,
        jitter=0.5,
        http_status_codes=[
            408,
            429,
            500,
            502,
            503,
            504,
        ],
    )

    http_options = types.HttpOptions(
        timeout=120000,
        retry_options=retry_options,
    )

    return genai.Client(
        api_key=settings.GEMINI_API_KEY,
        http_options=http_options,
    )


def generate_embedding(text: str) -> list[float]:
    if not text or not text.strip():
        raise ValueError("Embedding text cannot be empty.")

    client = get_gemini_client()

    result = client.models.embed_content(
        model=settings.EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            output_dimensionality=settings.EMBEDDING_DIMENSIONS
        ),
    )

    if not result.embeddings:
        raise RuntimeError("Gemini returned no embedding.")

    embedding = result.embeddings[0].values

    if len(embedding) != settings.EMBEDDING_DIMENSIONS:
        raise RuntimeError("Unexpected embedding dimensions.")

    return embedding
