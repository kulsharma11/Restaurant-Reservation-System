# app/models/table.py

from sqlalchemy import Column, Integer, String
from app.database import Base


class Table(Base):
    __tablename__ = "tables"

    id = Column(Integer, primary_key=True, index=True)
    table_number = Column(Integer, unique=True, nullable=False)
    capacity = Column(Integer, nullable=False)
    location = Column(String(50), nullable=False)  # "indoor" or "outdoor"

    def __repr__(self):
        return f"<Table #{self.table_number} capacity={self.capacity} location={self.location}>"
