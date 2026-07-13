"""Mock OpenAI-compatible embedding server for development.

Returns random vectors of configurable dimension (default: 1024).
Usage: uvicorn scripts.embedding_mock:app --host 0.0.0.0 --port 8001
"""

from __future__ import annotations

import os
import random

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Embedding Mock")

_VECTOR_SIZE = int(os.environ.get("VECTOR_SIZE", "1024"))
random.seed(42)  # deterministic for reproducibility


class EmbeddingRequest(BaseModel):
    input: str | list[str]
    model: str = "intfloat/multilingual-e5-large"


class EmbeddingData(BaseModel):
    object: str = "embedding"
    index: int = 0
    embedding: list[float]


class EmbeddingUsage(BaseModel):
    prompt_tokens: int = 0
    total_tokens: int = 0


class EmbeddingResponse(BaseModel):
    object: str = "list"
    data: list[EmbeddingData]
    model: str
    usage: EmbeddingUsage = EmbeddingUsage()


@app.post("/v1/embeddings")
async def embed(req: EmbeddingRequest) -> EmbeddingResponse:
    inputs = [req.input] if isinstance(req.input, str) else req.input
    data = [
        EmbeddingData(
            index=i,
            embedding=[random.uniform(-0.1, 0.1) for _ in range(_VECTOR_SIZE)],  # noqa: S311
        )
        for i in range(len(inputs))
    ]
    return EmbeddingResponse(data=data, model=req.model)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
