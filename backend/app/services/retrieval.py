"""Medication retrieval for the grounded RAG chatbot (Upgrade #7).

The chatbot is grounded - meaning Claude is NEVER allowed to invent facts.
It only paraphrases information that comes from rows we retrieve here.

Strategy:
  1. Pull keywords out of the user's question (very basic tokenizer; no stop
     words ML, just a list of common English words).
  2. Run a Postgres ILIKE search across name + active_ingredient + atc_code +
     description. We use ILIKE for portability; if/when we want fuzzy
     matching we can swap in pg_trgm without changing the interface.
  3. Score each medication by how many distinct keywords matched.
  4. Take the top K medications. These are the *only* facts Claude is allowed
     to use when answering.

A more elaborate version would use embeddings + pgvector. We deliberately
chose lexical retrieval because (a) our corpus is small (~200 medications),
(b) medication names and active ingredients are precise terms where lexical
match works well, and (c) the student can defend every step.
"""

from dataclasses import dataclass
from typing import Iterable

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.medication import Medication

TOP_K = 6
MIN_TOKEN_LEN = 3

_STOPWORDS = {
    "the", "and", "for", "with", "what", "which", "that", "this", "have", "has",
    "are", "any", "from", "about", "tell", "you", "can", "give", "show", "list",
    "same", "active", "ingredient", "medicine", "medication", "drug", "drugs",
    "alternative", "alternatives", "info", "information", "please", "would",
    "should", "could", "does", "doing", "they", "them", "their", "there",
}


def _tokenize(text: str) -> list[str]:
    words = []
    for raw in text.lower().replace(",", " ").replace(".", " ").split():
        cleaned = "".join(ch for ch in raw if ch.isalnum() or ch == "-")
        if len(cleaned) >= MIN_TOKEN_LEN and cleaned not in _STOPWORDS:
            words.append(cleaned)
    return words


@dataclass
class RetrievedMedication:
    medication: Medication
    matched_tokens: list[str]
    score: int


def retrieve(db: Session, query: str, limit: int = TOP_K) -> list[RetrievedMedication]:
    tokens = _tokenize(query)
    if not tokens:
        return []

    # Build the OR filter: any field matches any token.
    field_targets = [
        Medication.name,
        Medication.active_ingredient,
        Medication.atc_code,
        Medication.description,
        Medication.manufacturer,
    ]
    or_clauses = []
    for token in tokens:
        pattern = f"%{token}%"
        for field in field_targets:
            or_clauses.append(field.ilike(pattern))

    stmt = select(Medication).where(or_(*or_clauses)).limit(50)
    candidates = list(db.scalars(stmt).all())

    # Score each candidate by the number of distinct tokens it matches across
    # any field. This is a tiny TF-style ranker - boring, transparent, fine.
    scored: list[RetrievedMedication] = []
    for med in candidates:
        haystack = " ".join(
            filter(
                None,
                [
                    med.name,
                    med.active_ingredient,
                    med.atc_code,
                    med.description,
                    med.manufacturer,
                ],
            )
        ).lower()
        matched = [t for t in tokens if t in haystack]
        if matched:
            scored.append(RetrievedMedication(medication=med, matched_tokens=matched, score=len(matched)))

    scored.sort(key=lambda r: r.score, reverse=True)
    return scored[:limit]


def format_context(retrieved: Iterable[RetrievedMedication]) -> str:
    """Render retrieved medications as a plain-text block fed to Claude as the
    ONLY allowed source of facts."""
    lines: list[str] = []
    for r in retrieved:
        m = r.medication
        lines.append(
            f"- id={m.id} | name={m.name} | active_ingredient={m.active_ingredient}"
            f" | atc={m.atc_code or 'n/a'} | form={m.form} | strength={m.strength}"
            f" | manufacturer={m.manufacturer}"
            + (f" | description: {m.description}" if m.description else "")
        )
    return "\n".join(lines)
