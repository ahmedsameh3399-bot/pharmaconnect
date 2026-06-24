"""Grounded RAG chatbot orchestrator (Upgraded to Groq المجاني).

Flow on every user question:
  1. Persist the user's message.
  2. Retrieve top-K relevant medications from our DB (services.retrieval).
  3. Build a strict system prompt instructing Groq to ONLY use the provided
     context, and to refuse if the context can't answer the question.
  4. Send the prompt + a short rolling history of the chat to Groq.
  5. Persist the assistant's reply with a citations field listing the
     medication IDs we retrieved.
"""

import json
import logging
import os
from datetime import date

# استبدلنا مكتبة كلود بمكتبة Groq
from groq import Groq
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.chat import ChatMessage, ChatSession
from app.models.user import User
from app.services.retrieval import retrieve, format_context

log = logging.getLogger(__name__)

HISTORY_TURN_LIMIT = 6

SYSTEM_PROMPT = """You are Pharma Connect's expert medical and medication-information assistant.

You must communicate fluently and naturally in Arabic (preferring Egyptian/Standard Arabic as used by the user) or English. You act as an expert pharmacist who knows everything about medications, active ingredients, and alternative treatments.

You must follow these strict rules:
1. **Language**: Always respond in the same language the user is using. Respond in a friendly, clear, and professional Arabic.
2. **Symptom Complaints (ترشيح العلاج حسب الشكوى)**: If a user complains about a symptom, pain, or illness (e.g., "عندي صداع", "مغص", "كحة"), analyze the complaint and recommend the best, safest standard medications or OTC treatments. Explain briefly how each recommended medicine helps.
3. **Active Ingredients & Alternatives (المواد الفعالة والبدائل)**: When asked about any medication, always be ready to explain its active ingredient (المادة الفعالة). If the user asks for an alternative (بديل), provide generic alternatives (same active ingredient) or therapeutic alternatives (different ingredient but has the same effect).
4. **Knowledge Base**: First, check the provided CONTEXT block. If the medication or information is there, use it. If it is NOT in the context, do NOT say "I don't have enough information". Instead, use your own extensive, built-in medical and pharmacological knowledge to give a complete, perfect answer.
5. **Medical Disclaimer**: At the end of medical recommendations or diagnoses, always add a friendly disclaimer reminding the user to consult a physician or a licensed pharmacist to confirm exact dosages (e.g., "يرجى استشارة الطبيب أو الصيدلي للتأكد من الجرعة المناسبة لحالتك").
6. Keep your responses highly organized using bullet points and bold text for medicine names.
"""


class ChatbotDisabled(Exception):
    """Raised when API Key isn't configured."""


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
    """Return the last few turns formatted as Groq API messages."""
    msgs = [m for m in session.messages if m.role in ("user", "assistant")]
    if msgs and msgs[-1].role == "user":
        msgs = msgs[:-1]  
    trimmed = msgs[-(HISTORY_TURN_LIMIT * 2):]
    return [{"role": m.role, "content": m.content} for m in trimmed]


def ask(db: Session, user: User, session_id: int | None, message: str) -> ChatMessage:
    """Run one chatbot turn end-to-end. Caller commits the session."""
    
    # محاولة قراءة المفتاح من البيئة أو استخدام المفتاح القديم تيسيراً عليك
    groq_key = os.environ.get("GROQ_API_KEY") or getattr(settings, "anthropic_api_key", None)
    
    if not groq_key:
        raise ChatbotDisabled("Chatbot is not configured (GROQ_API_KEY missing).")

    _check_quota(db, user)

    session = _get_or_create_session(db, user, session_id)

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

    # تشغيل عميل Groq الجديد
    client = Groq(api_key=groq_key)
    try:
        # دمج الـ System Prompt في قائمة الرسائل لأن Groq يفضل هذا الهيكل
        full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history
        
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # الموديل الحديث والمجاني
            max_tokens=400,
            messages=full_messages,
        )
        reply_text = response.choices[0].message.content.strip()
        
    except Exception as exc:
        log.exception("Groq API call failed")
        reply_text = (
            "Sorry, the assistant is temporarily unavailable. "
            f"({type(exc).__name__})"
        )

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