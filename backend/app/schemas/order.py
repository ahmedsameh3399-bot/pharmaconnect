from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.order import OrderStatus
from app.schemas.medication import MedicationOut


class OrderItemIn(BaseModel):
    medication_id: int
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    distributor_id: int
    items: list[OrderItemIn] = Field(min_length=1)
    notes: str | None = Field(default=None, max_length=500)


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    medication: MedicationOut
    quantity: int
    unit_price: float
    discount_percent: float
    line_total: float


class OrderEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    from_status: str | None
    to_status: str
    note: str | None
    created_at: datetime


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    pharmacy_id: int
    distributor_id: int
    status: OrderStatus
    total_amount: float
    notes: str | None
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemOut]
    events: list[OrderEventOut]


class OrderStatusUpdate(BaseModel):
    new_status: OrderStatus
    note: str | None = Field(default=None, max_length=500)
