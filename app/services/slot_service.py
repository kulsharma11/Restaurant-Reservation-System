# app/services/slot_service.py

from sqlalchemy.orm import Session
from datetime import date
from app.models.table import Table
from app.models.reservation import Reservation
from app.config import TIME_SLOTS, ReservationStatus


def get_available_slots(db: Session, reservation_date: date, time_slot: str | None = None) -> list[dict]:
    """
    For each time slot (or selected slot), finds which tables are NOT booked on the given date.

    Strategy:
    1. Get all active reservations for that date (and slot, if provided)
    2. Collect the table_ids that are booked
    3. Return available tables for each applicable slot
    """
    query = db.query(Reservation).filter(
        Reservation.date == reservation_date,
        Reservation.status == ReservationStatus.ACTIVE.value
    )
    if time_slot:
        query = query.filter(Reservation.time_slot == time_slot)

    booked_reservations = query.all()

    # Build a lookup: { "18:00": {table_id_1, table_id_2}, "20:00": {table_id_3} }
    booked_by_slot: dict[str, set[int]] = {slot: set() for slot in TIME_SLOTS}
    for reservation in booked_reservations:
        booked_by_slot[reservation.time_slot].add(reservation.table_id)

    # Get all tables once
    all_tables = db.query(Table).all()

    # Determine slots to report
    slots_to_check = [time_slot] if time_slot else TIME_SLOTS

    # Build the response
    result = []
    for slot in slots_to_check:
        if slot not in TIME_SLOTS:
            continue
        available = [t for t in all_tables if t.id not in booked_by_slot[slot]]
        result.append({
            "date": reservation_date,
            "time_slot": slot,
            "available_tables": available
        })

    return result
