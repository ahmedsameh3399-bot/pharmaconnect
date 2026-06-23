from pydantic import BaseModel, ConfigDict, Field


class MedicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    active_ingredient: str
    atc_code: str | None
    form: str
    strength: str
    manufacturer: str
    description: str


class MedicationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    active_ingredient: str = Field(min_length=1, max_length=200)
    atc_code: str | None = Field(default=None, max_length=16)
    form: str = Field(min_length=1, max_length=60)
    strength: str = Field(min_length=1, max_length=60)
    manufacturer: str = Field(min_length=1, max_length=160)
    description: str = ""
