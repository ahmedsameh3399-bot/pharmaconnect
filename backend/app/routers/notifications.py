"""Server-Sent Events stream for real-time notifications.

The browser opens an EventSource connection to /notifications/stream with the
JWT in the Authorization header (or as a query param for browsers that don't
let EventSource set headers - we accept both).

This is intentionally simpler than WebSockets: SSE is one-directional
(server -> client), uses ordinary HTTP, and reconnects automatically. That's
exactly what we need for "tell me when something happens".
"""

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query, status
from jose import JWTError
from sse_starlette.sse import EventSourceResponse

from app.deps import get_db
from app.models.user import User
from app.security import decode_token
from app.services.notifications import hub

router = APIRouter(prefix="/notifications", tags=["notifications"])

HEARTBEAT_SECONDS = 15  # keep proxies from killing idle connections


@router.get("/stream")
async def stream(token: str = Query(..., description="JWT access token"), db=Depends(get_db)):
    """Stream notifications for the authenticated user as SSE events."""
    try:
        user_id = decode_token(token, expected_type="access")
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    user = db.get(User, user_id)
    if not user or not user.is_active or user.is_suspended:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not allowed")

    queue = await hub.subscribe(user_id)

    async def event_generator():
        try:
            while True:
                try:
                    notification = await asyncio.wait_for(queue.get(), timeout=HEARTBEAT_SECONDS)
                    yield {"event": "notification", "data": hub.serialize(notification)}
                except asyncio.TimeoutError:
                    # Comment line keeps the connection alive through proxies.
                    yield {"event": "ping", "data": "keepalive"}
        finally:
            await hub.unsubscribe(user_id, queue)

    return EventSourceResponse(event_generator())
