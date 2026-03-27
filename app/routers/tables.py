# app/routers/tables.py

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.table import TableCreate, TableResponse
from app.services import table_service

router = APIRouter()


@router.post("/", response_model=TableResponse, status_code=status.HTTP_201_CREATED)
def create_table(data: TableCreate, db: Session = Depends(get_db)):
    """
    Staff endpoint: Add a new table to the restaurant.

    - Validates table_number uniqueness
    - Validates capacity > 0
    - Validates location is indoor or outdoor
    """
    return table_service.create_table(db, data)


@router.get("/", response_model=list[TableResponse])
def list_tables(db: Session = Depends(get_db)):
    """Returns all tables in the restaurant."""
    return table_service.get_all_tables(db)
