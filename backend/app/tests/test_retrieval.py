"""Retrieval tests for the chatbot grounding layer."""

from app.models.medication import Medication
from app.services.retrieval import format_context, retrieve


def _seed(db):
    db.add_all([
        Medication(name="Panadol", active_ingredient="Paracetamol", atc_code="N02BE01",
                   form="Tablet", strength="500 mg", manufacturer="GSK", description="pain"),
        Medication(name="Cetal", active_ingredient="Paracetamol", atc_code="N02BE01",
                   form="Tablet", strength="500 mg", manufacturer="EIPICO", description="pain"),
        Medication(name="Brufen", active_ingredient="Ibuprofen", atc_code="M01AE01",
                   form="Tablet", strength="400 mg", manufacturer="Abbott", description="anti-inflammatory"),
    ])
    db.flush()


def test_alternatives_query_pulls_same_active_ingredient(db):
    _seed(db)
    results = retrieve(db, "alternatives for Panadol with same active ingredient paracetamol")
    names = {r.medication.name for r in results}
    # Both paracetamol products should be retrieved; Brufen should not lead.
    assert {"Panadol", "Cetal"}.issubset(names)
    assert results[0].medication.active_ingredient.lower().startswith("paracetamol")


def test_empty_query_returns_nothing(db):
    _seed(db)
    assert retrieve(db, "  ") == []


def test_format_context_renders_one_row_per_med(db):
    _seed(db)
    results = retrieve(db, "ibuprofen")
    rendered = format_context(results)
    assert "Brufen" in rendered
    assert "Ibuprofen" in rendered
