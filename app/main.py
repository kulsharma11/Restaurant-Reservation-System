# app/main.py

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base

# Import routers
from app.routers import tables, reservations

# Import domain exceptions for global handler registration
from app.exceptions import (
    TableNotFoundError,
    DuplicateTableError,
    CapacityExceededError,
    DoubleBookingError,
    NoTablesAvailableError,
    ReservationNotFoundError,
    AlreadyCancelledError,
    CancellationWindowError,
)

# Create all database tables on startup if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Restaurant Reservation API",
    description="A RESTful API for managing restaurant table reservations",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Exception Handlers ──────────────────────────────────────────────────────
# These catch domain exceptions from the service layer and convert them
# to proper HTTP responses. This is the ONLY place HTTP status codes
# are assigned to business errors.

@app.exception_handler(TableNotFoundError)
@app.exception_handler(ReservationNotFoundError)
async def not_found_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(DuplicateTableError)
@app.exception_handler(DoubleBookingError)
@app.exception_handler(NoTablesAvailableError)
async def conflict_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(CapacityExceededError)
@app.exception_handler(AlreadyCancelledError)
@app.exception_handler(CancellationWindowError)
async def bad_request_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


# ── Routers ──────────────────────────────────────────────────────────────────

app.include_router(tables.router, prefix="/tables", tags=["Tables"])
app.include_router(reservations.router, prefix="/reservations", tags=["Reservations"])


@app.get("/")
def root():
    return FileResponse("frontend/index.html")
