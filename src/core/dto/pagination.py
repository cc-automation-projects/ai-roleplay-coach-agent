"""Pagination models and utilities for list endpoints."""

from __future__ import annotations

import math
from typing import TypeVar

from pydantic import BaseModel, Field

_T = TypeVar("_T")


class PageParams(BaseModel):
    """Query parameters for paginated list endpoints."""

    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    size: int = Field(default=20, ge=1, le=100, description="Items per page")

    @property
    def skip(self) -> int:
        """Number of items to skip for the current page."""
        return (self.page - 1) * self.size

    @property
    def limit(self) -> int:
        """Number of items per page (alias for size)."""
        return self.size


class Page[T](BaseModel):
    """Paginated response wrapper."""

    items: list[_T]
    total: int
    page: int
    size: int

    @property
    def pages(self) -> int:
        """Total number of pages."""
        if self.total == 0:
            return 0
        return max(1, math.ceil(self.total / self.size))

    @classmethod
    def from_list(
        cls,
        items: list[_T],
        total: int,
        params: PageParams,
    ) -> Page[_T]:
        """Build a Page from a sliced items list and total count."""
        return cls(
            items=items,
            total=total,
            page=params.page,
            size=params.size,
        )


def paginate[T](
    items: list[_T],
    total: int | None = None,
    *,
    page: int = 1,
    size: int = 20,
) -> Page[_T]:
    """Convenience function to create a Page from a full list.

    Args:
        items: The items for the current page (already sliced).
        total: Total number of items across all pages.
               Defaults to ``len(items)`` if the list was pre-sliced.
        page: Current page number.
        size: Items per page.

    Returns:
        A Page instance with calculated metadata.
    """
    return Page(
        items=items,
        total=total if total is not None else len(items),
        page=page,
        size=size,
    )
