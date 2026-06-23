# Chatbot Design (Grounded RAG)

## Goal

Answer questions like "what alternatives to Panadol contain paracetamol?"
without ever inventing facts that aren't in our catalog.

## Flow

```
            ┌──────────────────────────────────────────────────────┐
            │            Pharmacy user sends a message              │
            └────────────────────────┬─────────────────────────────┘
                                     │
                                     ▼
                  ┌──────────────────────────────────┐
                  │ 1. Persist user message          │
                  └────────────────┬─────────────────┘
                                   ▼
                  ┌──────────────────────────────────┐
                  │ 2. Retrieve top-K medications    │
                  │    (services/retrieval.py)       │
                  │    - tokenize the question       │
                  │    - ILIKE search over           │
                  │      name + active_ingredient    │
                  │      + atc_code + description    │
                  │    - score by tokens matched     │
                  └────────────────┬─────────────────┘
                                   ▼
                  ┌──────────────────────────────────┐
                  │ 3. Build CONTEXT block: one      │
                  │    text line per medication      │
                  └────────────────┬─────────────────┘
                                   ▼
                  ┌──────────────────────────────────┐
                  │ 4. Call Claude with:             │
                  │    - strict system prompt        │
                  │    - last 6 turns of history     │
                  │    - "CONTEXT" + "QUESTION"      │
                  └────────────────┬─────────────────┘
                                   ▼
                  ┌──────────────────────────────────┐
                  │ 5. Persist assistant reply with  │
                  │    citations = retrieved IDs     │
                  └──────────────────────────────────┘
```

## The system prompt (the safety boundary)

The Claude model is told:

1. **Only use the CONTEXT.** No outside medical knowledge.
2. **Say "I don't have enough information"** when the context can't answer.
3. **Never give dosing or prescribing advice.** Defer to a professional.
4. **Cite by medication name inline.**

If the API key is missing the endpoint returns 503 rather than silently
guessing.

## Why lexical retrieval (not embeddings + vector DB)?

- Our corpus is ~200 medications - tiny.
- Medication names, active ingredients, and ATC codes are *precise terms*.
  Lexical match works well; embeddings would be over-engineering.
- A pgvector-based pipeline is harder to explain in a defense ("what's a
  cosine similarity over 1536-dim float vectors and why does it work?").

Trade-off: lexical retrieval misses synonyms. If we needed "fever reducer"
to find "antipyretic", we'd add an alias column or upgrade to embeddings.
For the graduation scope we don't need that.

## Why we still need Claude

We *could* return raw rows from the DB. But pharmacists want sentences,
not table dumps:

> "Both Cetal (Paracetamol 500 mg) and Adol (Paracetamol 500 mg) contain
> the same active ingredient as Panadol."

Claude's role is strictly *phrasing the retrieved facts as fluent English*.
We never depend on it knowing anything.

## Safety controls

- **Per-user daily quota** (`CHATBOT_DAILY_REQUEST_LIMIT`, default 50)
  caps cost and abuse.
- **UI disclaimer banner** on every chat page: "Informational only. Not
  medical advice."
- **Stored citations** (`chat_messages.citations`) let an auditor verify
  every assistant claim against the rows that produced it.
