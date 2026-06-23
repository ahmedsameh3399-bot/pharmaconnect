"""Models package.

Every model module is imported here so SQLAlchemy registers them on
`Base.metadata`. Without these imports, Alembic autogenerate would miss tables
that aren't referenced elsewhere yet.
"""

from app.models.user import User, UserRole  # noqa: F401
from app.models.pharmacy import Pharmacy  # noqa: F401
from app.models.distributor import Distributor  # noqa: F401
from app.models.medication import Medication  # noqa: F401
from app.models.offer import Offer  # noqa: F401
from app.models.order import Order, OrderItem, OrderStatus  # noqa: F401
from app.models.order_event import OrderEvent  # noqa: F401
from app.models.chat import ChatSession, ChatMessage  # noqa: F401
