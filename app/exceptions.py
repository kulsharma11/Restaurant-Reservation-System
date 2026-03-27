# app/exceptions.py

"""
Domain exceptions for the reservation system.

These are raised by the service layer and caught by the routers.
Services never import or raise FastAPI's HTTPException — this keeps
business logic decoupled from the HTTP framework (Dependency Inversion Principle).
"""


class TableNotFoundError(Exception):
    """Raised when a requested table does not exist."""
    def __init__(self, table_id: int):
        self.table_id = table_id
        super().__init__(f"Table with id {table_id} not found")


class DuplicateTableError(Exception):
    """Raised when attempting to create a table with a number that already exists."""
    def __init__(self, table_number: int):
        self.table_number = table_number
        super().__init__(f"Table number {table_number} already exists")


class CapacityExceededError(Exception):
    """Raised when guest count exceeds the table's capacity."""
    def __init__(self, table_number: int, capacity: int, guest_count: int):
        self.table_number = table_number
        self.capacity = capacity
        self.guest_count = guest_count
        super().__init__(
            f"Table {table_number} has capacity {capacity}, "
            f"but {guest_count} guests requested"
        )


class DoubleBookingError(Exception):
    """Raised when a table is already booked for the requested date and slot."""
    def __init__(self, table_number: int, date, time_slot: str):
        self.table_number = table_number
        self.date = date
        self.time_slot = time_slot
        super().__init__(
            f"Table {table_number} is already booked on {date} at {time_slot}"
        )


class NoTablesAvailableError(Exception):
    """Raised when smart assignment finds no suitable tables."""
    def __init__(self, guest_count: int, date, time_slot: str):
        self.guest_count = guest_count
        self.date = date
        self.time_slot = time_slot
        super().__init__(
            f"No available tables for {guest_count} guests "
            f"on {date} at {time_slot}"
        )


class ReservationNotFoundError(Exception):
    """Raised when a requested reservation does not exist."""
    def __init__(self, reservation_id: int):
        self.reservation_id = reservation_id
        super().__init__(f"Reservation {reservation_id} not found")


class AlreadyCancelledError(Exception):
    """Raised when attempting to cancel a reservation that is already cancelled."""
    def __init__(self, reservation_id: int):
        self.reservation_id = reservation_id
        super().__init__(f"Reservation {reservation_id} is already cancelled")


class CancellationWindowError(Exception):
    """Raised when cancellation is attempted too close to the reservation time."""
    def __init__(self, hours_required: int):
        self.hours_required = hours_required
        super().__init__(
            f"Cannot cancel — cancellations must be made at least "
            f"{hours_required} hours before the reservation"
        )
