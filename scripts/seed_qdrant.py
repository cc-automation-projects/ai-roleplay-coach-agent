# ruff: noqa: E501
"""Seed script: load test scripts into Qdrant with embeddings via RAGService."""

from __future__ import annotations

import asyncio
import hashlib
import logging
from pathlib import Path
from uuid import UUID

from infrastructure.qdrant.client import QdrantStore
from infrastructure.qdrant.rag_service import RAGService

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def _make_id(seed: str) -> UUID:
    return UUID(hashlib.md5(seed.encode(), usedforsecurity=False).hexdigest()[:32])


TEST_SCRIPTS: list[dict] = []

_SCRIPT_TEXTS: list[tuple[str, str, list[str], str]] = [
    ("tech-support-outage", "Tech Support - Internet Outage", ["tech-support", "outage", "level1"], "script_001.txt"),
    ("billing-dispute", "Billing - Disputed Charge", ["billing", "dispute", "credit"], "script_002.txt"),
    ("retention-cancel", "Retention - Cancel Subscription", ["retention", "cancellation", "churn"], "script_003.txt"),
    ("sales-upgrade", "Sales - Upgrade Pitch", ["sales", "upsell", "upgrade"], "script_004.txt"),
    ("escalation-complaint", "Complaint - Executive Escalation", ["complaint", "escalation", "executive"], "script_005.txt"),
    ("refund-processing", "Refund Processing", ["refund", "processing", "standard"], "script_006.txt"),
    ("new-account-setup", "New Account Setup", ["onboarding", "setup", "new-customer"], "script_007.txt"),
    ("troubleshooting-speed", "Technical Troubleshooting - Slow Speed", ["tech-support", "speed", "troubleshooting"], "script_008.txt"),
    ("outbound-followup", "Outbound Follow-up Call", ["outbound", "follow-up", "feedback"], "script_009.txt"),
    ("contract-renewal", "Contract Renewal Negotiation", ["b2b", "contract", "negotiation"], "script_010.txt"),
]

_SCRIPT_DIR = Path(__file__).resolve().parent

for seed, title, tags, filename in _SCRIPT_TEXTS:
    text_file = _SCRIPT_DIR / "seed_texts" / filename
    if text_file.exists():
        text = text_file.read_text(encoding="utf-8").strip()
    else:
        text = title
        logger.warning("Missing text file: %s", text_file)
    TEST_SCRIPTS.append({"seed": seed, "title": title, "text": text, "tags": tags})


async def main() -> None:
    store = QdrantStore()
    rag = RAGService(store=store)
    await rag.ensure_index()
    logger.info("Qdrant collection ready")
    indexed = 0
    for entry in TEST_SCRIPTS:
        script_id = _make_id(entry["seed"])
        try:
            await rag.index_script(
                script_id=script_id,
                text=entry["text"],
                metadata={"title": entry["title"], "tags": entry["tags"]},
            )
            indexed += 1
            logger.info("Indexed: %s (%s)", entry["title"], script_id)
        except (OSError, ValueError, RuntimeError) as exc:
            logger.warning("Failed to index %s: %s", entry["title"], exc)
    await store.close()
    logger.info("Seeding complete! %d scripts indexed in Qdrant", indexed)


if __name__ == "__main__":
    asyncio.run(main())
