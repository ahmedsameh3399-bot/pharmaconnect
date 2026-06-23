"""Grounded RAG chatbot orchestrator (Upgrade #7).

Flow on every user question:
  1. Persist the user's message.
  2. Retrieve top-K relevant medications from our DB (services.retrieval).
  3. Build a strict system prompt instructing Claude to ONLY use the provided
     context, and to refuse if the context can't answer the question.
  4. Send the prompt + a short rolling history of the chat to Claude.
  5. Persist the assistant's reply with a citations field listing the
     medication IDs we retrieved.

If the Anthropic API key isn't configured the endpoint disables itself with a
clear error rather than silently failing.
"""

import json
import logging
from datetime import date

from anthropic import Anthropic
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.chat import ChatMessage, ChatSession
from app.models.user import User
from app.services.retrieval import retrieve, format_context

log = logging.getLogger(__name__)

# Hard limit on conversational history we send back to Claude per turn so
# costs stay bounded and the model isn't distracted by ancient context.
HISTORY_TURN_LIMIT = 6

SYSTEM_PROMPT = """You are Pharma Connect's medication-information assistant.

You answer questions for pharmacy staff using ONLY the medication records
provided to you in the CONTEXT block. You must follow these rules:

1. Do NOT use any medical knowledge that is not present in the CONTEXT.
2. If the CONTEXT does not contain enough information, say:
   "I don't have enough information in our catalog to answer that."
3. Never give dosing recommendations, diagnostic advice, or prescription
   guidance. If asked, say:
   "I can describe what's in our catalog, but for medical advice please
    consult a licensed pharmacist or physician."
4. When the user asks about alternatives, list medications from the CONTEXT
   that share the same active_ingredient (or same ATC code if the active
   ingredient match returns nothing).
5. Cite the medication name you used inline, e.g. "Panadol Extra (paracetamol 500 mg)".
6. Keep answers concise (under 150 words) and factual.
"""


class ChatbotDisabled(Exception):
    """Raised when ANTHROPIC_API_KEY isn't configured."""


class ChatbotRateLimited(Exception):
    """Raised when a user has used up their daily question quota."""


def _check_quota(db: Session, user: User) -> None:
    today = date.today()
    stmt = (
        select(func.count(ChatMessage.id))
        .join(ChatSession, ChatSession.id == ChatMessage.session_id)
        .where(
            ChatSession.user_id == user.id,
            ChatMessage.role == "user",
            func.date(ChatMessage.created_at) == today,
        )
    )
    used_today = db.scalar(stmt) or 0
    if used_today >= settings.chatbot_daily_request_limit:
        raise ChatbotRateLimited(
            f"Daily limit reached ({settings.chatbot_daily_request_limit} questions)."
        )


def _get_or_create_session(db: Session, user: User, session_id: int | None) -> ChatSession:
    if session_id is not None:
        session = db.get(ChatSession, session_id)
        if session and session.user_id == user.id:
            return session
    session = ChatSession(user_id=user.id, title="New chat")
    db.add(session)
    db.flush()
    return session


def _build_history(session: ChatSession) -> list[dict]:
    """Return the last few turns formatted as Claude API messages."""
    # Walk the messages in chronological order, then take the trailing slice
    # so we keep the most recent context. Drop the assistant's most recent
    # message because we're about to generate a new one in its place.
    msgs = [m for m in session.messages if m.role in ("user", "assistant")]
    if msgs and msgs[-1].role == "user":
        msgs = msgs[:-1]  # we'll append the current user turn separately
    trimmed = msgs[-(HISTORY_TURN_LIMIT * 2):]
    return [{"role": m.role, "content": m.content} for m in trimmed]


def ask(db: Session, user: User, session_id: int | None, message: str) -> ChatMessage:
    """Run one chatbot turn end-to-end. Caller commits the session."""
    if not settings.chatbot_enabled:
        raise ChatbotDisabled("Chatbot is not configured (ANTHROPIC_API_KEY missing).")

    _check_quota(db, user)

    session = _get_or_create_session(db, user, session_id)

    # Persist the user message FIRST so it's stored even if Claude fails.
    user_msg = ChatMessage(session_id=session.id, role="user", content=message)
    db.add(user_msg)
    db.flush()

    retrieved = retrieve(db, message)
    context_block = format_context(retrieved) or "(no matching medications in catalog)"
    citation_ids = [r.medication.id for r in retrieved]

    history = _build_history(session)
    history.append(
        {
            "role": "user",
            "content": f"CONTEXT (the only facts you may use):\n{context_block}\n\nQUESTION: {message}",
        }
    )

    client = Anthropic(api_key=settings.anthropic_api_key)
    try:
        response = client.messages.create(
            model=settings.claude_model,
            max_tokens=400,
            system=SYSTEM_PROMPT,
            messages=history,
        )
        reply_text = "".join(
            block.text for block in response.content if getattr(block, "type", "") == "text"
        ).strip()
    except Exception as exc:
        log.exception("Claude API call failed")
        reply_text = (
            "Sorry, the assistant is temporarily unavailable. "
            f"({type(exc).__name__})"
        )

    # Auto-title the session on the first turn so the user's chat list isn't
    # all "New chat".
    if session.title == "New chat":
        session.title = message[:80]

    assistant_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=reply_text or "(no answer)",
        citations=json.dumps(citation_ids) if citation_ids else None,
    )
    db.add(assistant_msg)
    db.flush()
    return assistant_msg
