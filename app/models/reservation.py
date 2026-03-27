# app/models/reservation.py

from sqlalchemy import Column, Integer, String, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys — link to the tables and customers tables
    table_id = Column(Integer, ForeignKey("tables.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)

    # Reservation details
    date = Column(Date, nullable=False)
    time_slot = Column(String(10), nullable=False)       # e.g. "18:00"
    guest_count = Column(Integer, nullable=False)
    special_requests = Column(String(255), nullable=True)

    # Status: "active" or "cancelled"
    status = Column(String(20), nullable=False, default="active")

    # Automatically set when the reservation is created
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships — lets you do reservation.table and reservation.customer
    table = relationship("Table")
    customer = relationship("Customer", back_populates="reservations")

    def __repr__(self):
        return f"<Reservation id={self.id} table={self.table_id} date={self.date} slot={self.time_slot}>"
