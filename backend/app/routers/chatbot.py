"""Chatbot endpoints. Pharmacy-only feature (Upgrade #7)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.deps import get_db, require_pharmacy
from app.models.chat import ChatMessage, ChatSession
from app.models.user import User
from app.schemas.chat import ChatAskRequest, ChatAskResponse, ChatMessageOut, ChatSessionOut
from app.services.chatbot import ChatbotDisabled, ChatbotRateLimited, ask

router = APIRouter(prefix="/chatbot", tags=["chatbot"])


@router.post("/ask", response_model=ChatAskResponse)
def ask_endpoint(
    payload: ChatAskRequest,
    user: User = Depends(require_pharmacy),
    db: Session = Depends(get_db),
) -> ChatAskResponse:
    try:
        assistant_msg = ask(db, user, payload.session_id, payload.message)
    except ChatbotDisabled as e:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(e))
    except ChatbotRateLimited as e:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, str(e))
    db.commit()
    db.refresh(assistant_msg)
    return ChatAskResponse(
        session_id=assistant_msg.session_id,
        assistant_message=ChatMessageOut.model_validate(assistant_msg),
    )


@router.get("/sessions", response_model=list[ChatSessionOut])
def list_sessions(
    user: User = Depends(require_pharmacy),
    db: Session = Depends(get_db),
) -> list[ChatSession]:
    stmt = (
        select(ChatSession)
        .where(ChatSession.user_id == user.id)
        .order_by(ChatSession.created_at.desc())
    )
    return list(db.scalars(stmt).all())


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageOut])
def get_session_messages(
    session_id: int,
    user: User = Depends(require_pharmacy),
    db: Session = Depends(get_db),
) -> list[ChatMessage]:
    session = db.get(ChatSession, session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    return list(session.messages)
