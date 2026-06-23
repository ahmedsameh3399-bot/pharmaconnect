"""FastAPI application entrypoint.

All routers are mounted here. Auto-generated OpenAPI docs are exposed at /docs
(Swagger UI) and /redoc, satisfying the book's "Full API documentation"
non-functional requirement.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import (
    admin,
    auth,
    chatbot,
    medications,
    notifications,
    offers,
    orders,
    ranking,
    stock_forecast,
    users,
)

app = FastAPI(
    title="Pharma Connect API",
    description=(
        "B2B platform connecting pharmacies with pharmaceutical distributors. "
        "Browse this interactive documentation to try every endpoint."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    """Liveness probe used by Docker healthchecks and uptime monitors."""
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(medications.router)
app.include_router(offers.router)
app.include_router(ranking.router)
app.include_router(orders.router)
app.include_router(notifications.router)
app.include_router(stock_forecast.router)
app.include_router(chatbot.router)
app.include_router(admin.router)
