"""ScriptNode — tree structure for branching scenario scripts."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum, auto
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from core.utils import utcnow


class NodeType(StrEnum):
    """Semantic type of a script node."""

    GREETING = auto()
    QUESTION = auto()
    INSTRUCTION = auto()
    OBJECTION_RESPONSE = auto()
    CLOSING = auto()
    BRANCH = auto()
    CONDITIONAL = auto()
    TERMINAL = auto()


class ScriptNode(BaseModel):
    """A single node in a branching script tree.

    Each node represents one logical step in the script (greeting,
    question, instruction, etc.). Nodes form a tree via ``parent_id``,
    and a node may have multiple children (branches) linked by
    ``next_node_ids``.

    Example structure::

        ScriptNode(id=A, node_type=GREETING)
        ├── ScriptNode(id=B, node_type=QUESTION, keywords=["billing"])
        │   └── ScriptNode(id=D, node_type=INSTRUCTION)
        └── ScriptNode(id=C, node_type=QUESTION, keywords=["technical"])
            └── ScriptNode(id=E, node_type=INSTRUCTION)
    """

    id: UUID = Field(default_factory=uuid4)
    scenario_id: UUID
    node_type: NodeType = NodeType.INSTRUCTION

    # The operator-facing text for this step (instruction, question, …)
    text: str = Field(min_length=1)

    # Tree structure
    parent_id: UUID | None = None
    next_node_ids: list[UUID] = Field(default_factory=list)

    # If CONDITIONAL — keywords that route to this branch
    keywords: list[str] = Field(default_factory=list)

    # Order among siblings
    order: int = 0

    # Expected best-practice keywords for scoring this node
    expected_keywords: list[str] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    # ── Helpers ─────────────────────────────────────────────────────────

    def is_root(self) -> bool:
        """Return True if this is the root node (no parent)."""
        return self.parent_id is None

    def add_child(self, child_id: UUID) -> None:
        """Link a child node as a next step."""
        if child_id not in self.next_node_ids:
            self.next_node_ids.append(child_id)


class ScriptNodeCreate(BaseModel):
    """DTO for creating a script node."""

    scenario_id: UUID
    node_type: NodeType = NodeType.INSTRUCTION
    text: str = Field(min_length=1)
    parent_id: UUID | None = None
    keywords: list[str] = Field(default_factory=list)
    order: int = 0
    expected_keywords: list[str] = Field(default_factory=list)


class ScriptNodeUpdate(BaseModel):
    """DTO for updating a script node. All fields optional."""

    node_type: NodeType | None = None
    text: str | None = None
    parent_id: UUID | None = None
    next_node_ids: list[UUID] | None = None
    keywords: list[str] | None = None
    order: int | None = None
    expected_keywords: list[str] | None = None
