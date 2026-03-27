# app/config.py

from enum import Enum

# Fixed time slots the restaurant operates
TIME_SLOTS = ["18:00", "20:00", "22:00"]

# How many hours before a slot the customer must cancel by
CANCELLATION_WINDOW_HOURS = 2

# Valid location values for tables
class TableLocation(str, Enum):
    INDOOR = "indoor"
    OUTDOOR = "outdoor"

# Valid reservation statuses
class ReservationStatus(str, Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
