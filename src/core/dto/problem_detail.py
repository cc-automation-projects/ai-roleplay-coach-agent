"""RFC 9457 (RFC 7807) Problem Details for HTTP APIs."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ProblemDetail(BaseModel):
    """Standard error response per RFC 9457 (Problem Details)."""

    type: str = Field(
        default="about:blank",
        description="URI reference identifying the problem type",
    )
    title: str = Field(description="Short human-readable summary")
    status: int = Field(description="HTTP status code", ge=100, lt=600)
    detail: str | None = Field(default=None, description="Human-readable explanation")
    instance: str | None = Field(
        default=None, description="URI reference identifying the specific occurrence"
    )

    model_config = {"extra": "allow"}
