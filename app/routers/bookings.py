from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, time
import crud, schemas, models, security, deps

router = APIRouter(prefix="/api/v1/bookings", tags=["bookings"])

@router.post("/", response_model=schemas.Booking)
def book_room(
    booking: schemas.BookingCreate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    # Set the user_id from the authenticated user if not provided
    if not booking.user_id:
        booking.user_id = current_user.id
    # Only admins can book on behalf of others
    if booking.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to book for other users.")
    # Validate slot
    if booking.slot_start < time(9, 0) or booking.slot_end > time(18, 0):
        raise HTTPException(status_code=400, detail="Booking slot must be between 09:00 and 18:00.")
    if booking.slot_start >= booking.slot_end:
        raise HTTPException(status_code=400, detail="End time must be after start time.")
    # Business logic for room allocation is in crud.create_booking
    db_booking = crud.create_booking(db, booking)
    return db_booking

@router.get("/", response_model=List[schemas.Booking])
def get_bookings(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    if current_user.is_admin:
        return crud.get_bookings(db, skip=skip, limit=limit)
    else:
        return crud.get_bookings(db, skip=skip, limit=limit, user_id=current_user.id)

@router.delete("/{booking_id}", response_model=schemas.Booking)
def cancel_booking(
    booking_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    booking = crud.get_booking(db, booking_id)
    if not booking or not booking.is_active:
        raise HTTPException(status_code=404, detail="Booking not found.")
    # Only admin or owner can cancel
    if not current_user.is_admin and booking.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to cancel this booking.")
    return crud.cancel_booking(db, booking_id)
