"""In-process notification hub (Upgrade #5).

A simple publish/subscribe hub backed by per-user asyncio.Queue objects. The
SSE endpoint creates a subscription for the current user; service code calls
`publish(user_id, event)` whenever something interesting happens (order placed,
status changed, etc.) and the event is streamed to every active subscription
for that user.

This is intentionally in-memory: it works on a single backend process. For
multi-process scale-out you'd replace this hub with Redis pub/sub. We accept
the single-process limit because it's vastly simpler to defend and matches the
"99% uptime, modest concurrent users" target in the book.

An email fallback is sent for key events so an offline user still finds out
when an order arrives.
"""

import asyncio
import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class Notification:
    type: str  # e.g. "order.created", "order.status_changed"
    payload: dict[str, Any]


class NotificationHub:
    def __init__(self) -> None:
        # Multiple subscriptions per user are allowed (e.g. user has the app
        # open in two browser tabs), so we keep a list of queues per user_id.
        self._subscribers: dict[int, list[asyncio.Queue[Notification]]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def subscribe(self, user_id: int) -> asyncio.Queue[Notification]:
        queue: asyncio.Queue[Notification] = asyncio.Queue()
        async with self._lock:
            self._subscribers[user_id].append(queue)
        return queue

    async def unsubscribe(self, user_id: int, queue: asyncio.Queue[Notification]) -> None:
        async with self._lock:
            if queue in self._subscribers.get(user_id, []):
                self._subscribers[user_id].remove(queue)

    def publish(self, user_id: int, notification: Notification) -> None:
        """Fire-and-forget. Called from synchronous request handlers; we use
        put_nowait so we never block a request on a slow subscriber."""
        for queue in self._subscribers.get(user_id, []):
            try:
                queue.put_nowait(notification)
            except asyncio.QueueFull:  # pragma: no cover - default Queue is unbounded
                pass

    @staticmethod
    def serialize(notification: Notification) -> str:
        return json.dumps({"type": notification.type, "payload": notification.payload})


# Module-level singleton. Importers get the same hub instance everywhere.
hub = NotificationHub()
