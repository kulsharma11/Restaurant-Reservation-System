# app/routers/reservations.py

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from datetime import date
from app.database import get_db
from app.schemas.reservation import ReservationCreate, ReservationResponse, AvailableSlotResponse
from app.services import reservation_service, slot_service

router = APIRouter()


@router.get("/available", response_model=list[AvailableSlotResponse])
def get_available_slots(date: date, time_slot: str | None = None, db: Session = Depends(get_db)):
    """
    Returns all (or one) time slots for a given date, with available tables per slot.

    Usage:
      GET /reservations/available?date=2026-04-10
      GET /reservations/available?date=2026-04-10&time_slot=18:00
    """
    return slot_service.get_available_slots(db, date, time_slot)


@router.post("/", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
def create_reservation(data: ReservationCreate, db: Session = Depends(get_db)):
    """
    Book a table. If table_id is not provided, smart assignment finds
    the smallest available table that fits the guest count.

    Returns the full reservation with table and customer details.
    """
    return reservation_service.create_reservation(db, data)


@router.get("/{reservation_id}", response_model=ReservationResponse)
def get_reservation(reservation_id: int, db: Session = Depends(get_db)):
    """Fetch details of a specific reservation by ID."""
    return reservation_service.get_reservation(db, reservation_id)


@router.delete("/{reservation_id}", response_model=ReservationResponse)
def cancel_reservation(reservation_id: int, db: Session = Depends(get_db)):
    """
    Cancel a reservation.

    Rules enforced:
    - Reservation must be active
    - Must cancel at least 2 hours before the time slot
    """
    return reservation_service.cancel_reservation(db, reservation_id)
