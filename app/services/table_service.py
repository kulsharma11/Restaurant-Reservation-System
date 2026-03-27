# app/services/table_service.py

from sqlalchemy.orm import Session
from app.models.table import Table
from app.schemas.table import TableCreate
from app.exceptions import DuplicateTableError


def create_table(db: Session, data: TableCreate) -> Table:
    """
    Creates a new table. Raises DuplicateTableError if table_number already exists.
    The database has a unique constraint on table_number, but we check
    first to return a clear error message instead of a raw DB error.
    """
    existing = db.query(Table).filter(Table.table_number == data.table_number).first()
    if existing:
        raise DuplicateTableError(data.table_number)

    table = Table(
        table_number=data.table_number,
        capacity=data.capacity,
        location=data.location.value  # .value converts enum to string "indoor"/"outdoor"
    )
    db.add(table)
    db.commit()
    db.refresh(table)  # Refresh loads the auto-generated id back into the object
    return table


def get_all_tables(db: Session) -> list[Table]:
    """Returns all registered tables."""
    return db.query(Table).all()
