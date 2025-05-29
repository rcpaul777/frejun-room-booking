from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, time, timedelta
from schemas import BookingCreate, Booking
import models, crud, deps
from security import get_current_user

router = APIRouter(prefix="/api/v1/bookings", tags=["bookings"])

@router.post("/", response_model=Booking)
def book_room(
    booking: BookingCreate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Set the user_id from the authenticated user if not provided
    if not booking.user_id:
        booking.user_id = current_user.id
    
    # Only admins can book on behalf of other users
    if booking.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to book for other users"
        )

    # Business logic for room allocation
    # 1. Validate slot
    if booking.slot_start < time(9, 0) or booking.slot_end > time(18, 0):
        raise HTTPException(status_code=400, detail="Slot must be between 9:00 and 18:00")
    if booking.slot_start >= booking.slot_end:
        raise HTTPException(status_code=400, detail="Invalid slot time")

    # 2. Room allocation logic
    rooms = crud.get_rooms_by_type(db, booking.room_type)
    if not rooms:
        raise HTTPException(status_code=404, detail="No rooms of this type")

    # 3. Check for available rooms
    available_rooms = crud.get_available_rooms(
        db, booking.slot_date, booking.slot_start, booking.slot_end, booking.room_type
    )
    if not available_rooms:
        raise HTTPException(status_code=400, detail="No available room for the selected slot and type.")

    # 4. Booking logic per room type
    if booking.room_type == "private":
        # Only individual users
        if not booking.user_id:
            raise HTTPException(status_code=400, detail="User ID required for private room")
        # Prevent double booking
        user_bookings = db.query(models.Booking).filter(
            models.Booking.user_id == booking.user_id,
            models.Booking.slot_date == booking.slot_date,
            models.Booking.slot_start < booking.slot_end,
            models.Booking.slot_end > booking.slot_start,
            models.Booking.is_active == True
        ).first()
        if user_bookings:
            raise HTTPException(status_code=400, detail="User already has a booking in this slot")
        # Assign first available room
        room = available_rooms[0]
        db_booking = models.Booking(
            room_id=room.id,
            user_id=booking.user_id,
            slot_date=booking.slot_date,
            slot_start=booking.slot_start,
            slot_end=booking.slot_end
        )
        db.add(db_booking)
        db.commit()
        db.refresh(db_booking)
        return db_booking

    elif booking.room_type == "conference":
        # Only teams of 3+ (excluding children <10)
        if not booking.team_id:
            raise HTTPException(status_code=400, detail="Team ID required for conference room")
        team = crud.get_team(db, booking.team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        headcount = sum(1 for m in team.members)
        seat_count = sum(1 for m in team.members if m.age >= 10)
        if headcount < 3:
            raise HTTPException(status_code=400, detail="Conference room requires team size >= 3")
        # Prevent double booking
        team_bookings = db.query(models.Booking).filter(
            models.Booking.team_id == booking.team_id,
            models.Booking.slot_date == booking.slot_date,
            models.Booking.slot_start < booking.slot_end,
            models.Booking.slot_end > booking.slot_start,
            models.Booking.is_active == True
        ).first()
        if team_bookings:
            raise HTTPException(status_code=400, detail="Team already has a booking in this slot")
        # Assign first available room
        room = available_rooms[0]
        db_booking = models.Booking(
            room_id=room.id,
            team_id=booking.team_id,
            slot_date=booking.slot_date,
            slot_start=booking.slot_start,
            slot_end=booking.slot_end
        )
        db.add(db_booking)
        db.commit()
        db.refresh(db_booking)
        return db_booking

    elif booking.room_type == "shared":
        # Check capacity
        room = available_rooms[0]
        existing_bookings = crud.get_overlapping_bookings(
            db, room.id, booking.slot_date, booking.slot_start, booking.slot_end
        )
        if len(existing_bookings) >= room.capacity:
            raise HTTPException(status_code=400, detail="Shared room is at full capacity for this slot")
        
        # Create booking
        db_booking = models.Booking(
            room_id=room.id,
            user_id=booking.user_id,
            slot_date=booking.slot_date,
            slot_start=booking.slot_start,
            slot_end=booking.slot_end
        )
        db.add(db_booking)
        db.commit()
        db.refresh(db_booking)
        return db_booking

@router.get("/", response_model=List[Booking])
def get_bookings(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get all active bookings. Admins see all, users see only their own."""
    if current_user.is_admin:
        return crud.get_bookings(db, skip=skip, limit=limit)
    return crud.get_user_bookings(db, user_id=current_user.id, skip=skip, limit=limit)

@router.delete("/{booking_id}", response_model=Booking)
def cancel_booking(
    booking_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Cancel a booking"""
    booking = crud.get_booking(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Only the booking owner or admin can cancel
    if booking.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to cancel this booking"
        )
    
    # Check if booking is in the future
    if booking.slot_date < date.today():
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel past bookings"
        )
    
    # Soft delete the booking
    booking.is_active = False
    db.commit()
    db.refresh(booking)
    return booking
