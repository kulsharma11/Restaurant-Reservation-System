# app/services/reservation_service.py

from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from app.models.table import Table
from app.models.customer import Customer
from app.models.reservation import Reservation
from app.schemas.reservation import ReservationCreate
from app.config import CANCELLATION_WINDOW_HOURS, ReservationStatus
from app.exceptions import (
    TableNotFoundError,
    CapacityExceededError,
    DoubleBookingError,
    NoTablesAvailableError,
    ReservationNotFoundError,
    AlreadyCancelledError,
    CancellationWindowError,
)


# ── Smart Assignment ──────────────────────────────────────────────────────────

def smart_assign_table(
    db: Session,
    reservation_date: date,
    time_slot: str,
    guest_count: int
) -> Table:
    """
    Finds the smallest available table that fits the guest count.

    Steps:
    1. Find all table_ids already booked for this date + slot
    2. Query tables where capacity >= guest_count AND id NOT IN booked set
    3. Order by capacity ASC → first result is the smallest fitting table
    4. Raise NoTablesAvailableError if no table found
    """
    # Step 1: Find booked table IDs for this date + slot
    booked_table_ids = (
        db.query(Reservation.table_id)
        .filter(
            Reservation.date == reservation_date,
            Reservation.time_slot == time_slot,
            Reservation.status == ReservationStatus.ACTIVE.value
        )
        .all()
    )
    # .all() returns a list of tuples like [(1,), (3,)], extract just the IDs
    booked_ids = {row[0] for row in booked_table_ids}

    # Step 2 & 3: Smallest fitting available table
    query = db.query(Table).filter(Table.capacity >= guest_count)
    if booked_ids:
        query = query.filter(Table.id.notin_(booked_ids))
    table = query.order_by(Table.capacity.asc()).first()

    # Step 4: No table found
    if not table:
        raise NoTablesAvailableError(guest_count, reservation_date, time_slot)

    return table


# ── Create Reservation ────────────────────────────────────────────────────────

def create_reservation(db: Session, data: ReservationCreate) -> Reservation:
    """
    Creates a reservation. Validates capacity and double-booking.
    Uses smart assignment if no table_id is provided.
    """
    # Determine the table to use
    if data.table_id is not None:
        # Customer picked a specific table — validate it exists
        table = db.query(Table).filter(Table.id == data.table_id).first()
        if not table:
            raise TableNotFoundError(data.table_id)

        # Check capacity — cannot seat more guests than the table holds
        if data.guest_count > table.capacity:
            raise CapacityExceededError(table.table_number, table.capacity, data.guest_count)

        # Check for double-booking — same table, same date, same slot, active status
        conflict = (
            db.query(Reservation)
            .filter(
                Reservation.table_id == data.table_id,
                Reservation.date == data.date,
                Reservation.time_slot == data.time_slot,
                Reservation.status == ReservationStatus.ACTIVE.value
            )
            .first()
        )
        if conflict:
            raise DoubleBookingError(table.table_number, data.date, data.time_slot)
    else:
        # No table specified — use smart assignment
        table = smart_assign_table(db, data.date, data.time_slot, data.guest_count)

    # Find or create the customer record
    customer = db.query(Customer).filter(Customer.email == data.customer.email).first()
    if not customer:
        customer = Customer(
            name=data.customer.name,
            email=data.customer.email,
            phone=data.customer.phone
        )
        db.add(customer)
        db.flush()  # flush assigns customer.id without committing the transaction

    # Create the reservation
    reservation = Reservation(
        table_id=table.id,
        customer_id=customer.id,
        date=data.date,
        time_slot=data.time_slot,
        guest_count=data.guest_count,
        special_requests=data.special_requests,
        status=ReservationStatus.ACTIVE.value
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    return reservation


# ── Get Reservation ───────────────────────────────────────────────────────────

def get_reservation(db: Session, reservation_id: int) -> Reservation:
    """Fetches a single reservation by ID. Raises ReservationNotFoundError if not found."""
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise ReservationNotFoundError(reservation_id)
    return reservation


# ── Cancel Reservation ────────────────────────────────────────────────────────

def cancel_reservation(db: Session, reservation_id: int) -> Reservation:
    """
    Cancels a reservation. Enforces the 2-hour cancellation window.

    Rules:
    - Reservation must exist
    - Reservation must currently be active (not already cancelled)
    - Current time must be at least CANCELLATION_WINDOW_HOURS before the slot
    """
    reservation = get_reservation(db, reservation_id)

    # Already cancelled
    if reservation.status == ReservationStatus.CANCELLED.value:
        raise AlreadyCancelledError(reservation_id)

    # Build a datetime for when the slot starts
    slot_hour, slot_minute = map(int, reservation.time_slot.split(":"))
    slot_datetime = datetime(
        reservation.date.year,
        reservation.date.month,
        reservation.date.day,
        slot_hour,
        slot_minute
    )

    # Check cancellation window
    cancellation_deadline = slot_datetime - timedelta(hours=CANCELLATION_WINDOW_HOURS)
    if datetime.now() > cancellation_deadline:
        raise CancellationWindowError(CANCELLATION_WINDOW_HOURS)

    reservation.status = ReservationStatus.CANCELLED.value
    db.commit()
    db.refresh(reservation)
    return reservation
