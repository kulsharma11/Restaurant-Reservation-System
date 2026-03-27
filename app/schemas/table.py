# app/schemas/table.py

from pydantic import BaseModel, Field
from app.config import TableLocation


class TableCreate(BaseModel):
    """Schema for POST /tables — what the staff sends to create a table."""
    table_number: int = Field(..., gt=0, description="Must be a positive integer")
    capacity: int = Field(..., gt=0, le=20, description="Between 1 and 20")
    location: TableLocation = Field(..., description="'indoor' or 'outdoor'")


class TableResponse(BaseModel):
    """Schema for responses — what the API returns about a table."""
    id: int
    table_number: int
    capacity: int
    location: str

    model_config = {"from_attributes": True}
    # from_attributes=True lets Pydantic read data from SQLAlchemy model
    # instances (which use attribute access) instead of dicts
