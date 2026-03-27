# app/models/customer.py

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)  # unique ensures one record per email
    phone = Column(String(20), nullable=True)

    # One customer can have many reservations
    reservations = relationship("Reservation", back_populates="customer")

    def __repr__(self):
        return f"<Customer {self.name} ({self.email})>"
