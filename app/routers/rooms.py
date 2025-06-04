from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import date, time, datetime
import crud, schemas, models, security, deps

router = APIRouter(prefix="/api/v1/rooms", tags=["rooms"])

def get_admin_user(current_user: models.User = Depends(security.get_current_user)) -> models.User:
    """Dependency to check if the user is an admin"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can perform this operation"
        )
    return current_user

@router.get("/available/", response_model=List[schemas.Room])
def available_rooms(
    slot_date: date = Query(...),
    slot_start: time = Query(...),
    slot_end: time = Query(...),
    room_type: str = Query(...),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    rooms = crud.get_available_rooms(db, slot_date, slot_start, slot_end, room_type)
    return [schemas.Room(
        id=room.id,
        room_type=room.room_type.value if hasattr(room.room_type, 'value') else room.room_type,
        capacity=room.capacity,
        name=room.name
    ) for room in rooms]

@router.get("/", response_model=List[schemas.Room])
def get_all_rooms(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    rooms = crud.get_all_rooms(db)
    return [schemas.Room(
        id=room.id,
        room_type=room.room_type.value if hasattr(room.room_type, 'value') else room.room_type,
        capacity=room.capacity,
        name=room.name
    ) for room in rooms]

@router.post("/", response_model=schemas.Room)
def create_room(
    room: schemas.RoomBase,
    db: Session = Depends(deps.get_db),
    admin_user: models.User = Depends(get_admin_user)
):
    return crud.create_room(db, room)

@router.put("/{room_id}", response_model=schemas.Room)
def update_room(
    room_id: int,
    room: schemas.RoomBase,
    db: Session = Depends(deps.get_db),
    admin_user: models.User = Depends(get_admin_user)
):
    return crud.update_room(db, room_id, room)

@router.delete("/{room_id}", response_model=schemas.Room)
def delete_room(
    room_id: int,
    db: Session = Depends(deps.get_db),
    admin_user: models.User = Depends(get_admin_user)
):
    return crud.delete_room(db, room_id)

@router.get("/status/", response_model=List[dict])
def get_rooms_status(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Returns all rooms with their availability status for today (current date, 09:00-18:00),
    considering all bookings. Used for the dashboard's 'Show Available Workspace Rooms' feature.
    """
    today = date.today()
    slot_start = time(9, 0)
    slot_end = time(18, 0)
    rooms = crud.get_all_rooms(db)
    bookings = crud.get_bookings_for_date(db, today)
    booked_room_ids = set()
    for booking in bookings:
        if booking.is_active and not (booking.slot_end <= slot_start or booking.slot_start >= slot_end):
            booked_room_ids.add(booking.room_id)
    result = []
    for room in rooms:
        # Room number naming convention
        if room.room_type == 'private' or (hasattr(room.room_type, 'value') and room.room_type.value == 'private'):
            prefix = 'p'
        elif room.room_type == 'conference' or (hasattr(room.room_type, 'value') and room.room_type.value == 'conference'):
            prefix = 'c'
        elif room.room_type == 'shared' or (hasattr(room.room_type, 'value') and room.room_type.value == 'shared'):
            prefix = 'sd'
        else:
            prefix = 'r'
        room_number = f"{prefix}{room.id}"
        is_available = room.id not in booked_room_ids
        result.append({
            'id': room.id,
            'room_type': room.room_type.value if hasattr(room.room_type, 'value') else room.room_type,
            'capacity': room.capacity,
            'name': room.name,
            'room_number': room_number,
            'is_available': is_available
        })
    return result
