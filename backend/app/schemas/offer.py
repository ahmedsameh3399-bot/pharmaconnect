from pydantic import BaseModel, ConfigDict, Field

from app.schemas.medication import MedicationOut


class OfferUpsert(BaseModel):
    """Used by distributors to create or update their offer for a medication."""

    medication_id: int
    unit_price: float = Field(gt=0)
    discount_percent: float = Field(ge=0, le=100, default=0)
    stock: int = Field(ge=0, default=0)


class OfferOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    distributor_id: int
    medication_id: int
    unit_price: float
    discount_percent: float
    stock: int
    final_unit_price: float
    medication: MedicationOut


class DistributorBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_name: str
    reliability_score: float


class RankedOfferOut(BaseModel):
    """One row in the comparison view: an offer plus its score breakdown."""

    model_config = ConfigDict(from_attributes=True)
    offer_id: int
    distributor: DistributorBrief
    unit_price: float
    discount_percent: float
    final_unit_price: float
    stock: int
    # Breakdown fields so the UI can render a "why this rank?" tooltip.
    price_score: float
    stock_score: float
    reliability_score: float
    total_score: float
