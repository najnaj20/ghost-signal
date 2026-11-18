"""Extractor interface (FR-2.5). Heuristic is the v1 default; an LLM extractor is an upgrade path only."""
from dataclasses import dataclass
from typing import Protocol

TYPES = ("company", "technology", "disease", "product", "person")


@dataclass(frozen=True)
class Entity:
    name: str
    type: str


@dataclass(frozen=True)
class Claim:
    a: Entity
    b: Entity  # a == b means "this document mentions a"
    label: str
    claim_text: str
    evidence_quote: str  # verbatim substring of the document text


class Extractor(Protocol):
    def extract(self, text: str) -> list[Claim]: ...


def keep(claims, text):
    """FR-2.3: drop any claim whose quote is empty or not verbatim in the source text."""
    return [c for c in claims if c.evidence_quote and c.evidence_quote in text]
