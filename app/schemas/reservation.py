# app/schemas/reservation.py

from pydantic import BaseModel, Field, field_validator
from datetime import date, datetime
from typing import Optional
from app.config import TIME_SLOTS
from app.schemas.table import TableResponse


class CustomerInfo(BaseModel):
    """Embedded in reservation requests — customer details."""
    name: str = Field(..., min_length=1)
    email: str = Field(..., description="Customer email address")
    phone: Optional[str] = None


class ReservationCreate(BaseModel):
    """Schema for POST /reservations."""
    date: date
    time_slot: str
    guest_count: int = Field(..., gt=0)
    table_id: Optional[int] = None       # If None, smart assignment is used
    special_requests: Optional[str] = None
    customer: CustomerInfo

    @field_validator("time_slot")
    @classmethod
    def time_slot_must_be_valid(cls, v):
        if v not in TIME_SLOTS:
            raise ValueError(f"time_slot must be one of {TIME_SLOTS}")
        return v

    @field_validator("date")
    @classmethod
    def date_must_not_be_in_past(cls, v):
        if v < date.today():
            raise ValueError("Reservation date must be today or in the future")
        return v


class CustomerSummary(BaseModel):
    """Compact customer info embedded in reservation responses."""
    id: int
    name: str
    email: str
    phone: Optional[str]

    model_config = {"from_attributes": True}


class TableSummary(BaseModel):
    """Compact table info embedded in reservation responses."""
    id: int
    table_number: int
    capacity: int
    location: str

    model_config = {"from_attributes": True}


class ReservationResponse(BaseModel):
    """Schema for responses — full reservation details."""
    id: int
    date: date
    time_slot: str
    guest_count: int
    special_requests: Optional[str]
    status: str
    created_at: datetime
    table: TableSummary
    customer: CustomerSummary

    model_config = {"from_attributes": True}


class AvailableSlotResponse(BaseModel):
    """Schema for GET /reservations/available response."""
    date: date
    time_slot: str
    available_tables: list[TableResponse]
