from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import date, time
from schemas import Room, RoomBase
import crud, deps
from security import get_current_user
from models import User

router = APIRouter(prefix="/api/v1/rooms", tags=["rooms"])

def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to check if the user is an admin"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can perform this operation"
        )
    return current_user

@router.get("/available/", response_model=List[Room])
def available_rooms(
    slot_date: date = Query(...),
    slot_start: time = Query(...),
    slot_end: time = Query(...),
    room_type: str = Query(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(get_current_user)
):
    rooms = crud.get_available_rooms(db, slot_date, slot_start, slot_end, room_type)
    return [Room(
        id=room.id,
        room_type=room.room_type.value if hasattr(room.room_type, 'value') else room.room_type,
        capacity=room.capacity,
        name=room.name
    ) for room in rooms]

@router.get("/", response_model=List[Room])
def get_all_rooms(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(get_current_user)
):
    rooms = crud.get_all_rooms(db)
    return [Room(
        id=room.id,
        room_type=room.room_type.value if hasattr(room.room_type, 'value') else room.room_type,
        capacity=room.capacity,
        name=room.name
    ) for room in rooms]

@router.post("/", response_model=Room)
def create_room(
    room: RoomBase,
    db: Session = Depends(deps.get_db),
    admin_user: User = Depends(get_admin_user)
):
    db_room = crud.create_room(db, room)
    return Room(
        id=db_room.id,
        room_type=db_room.room_type.value if hasattr(db_room.room_type, 'value') else db_room.room_type,
        capacity=db_room.capacity,
        name=db_room.name
    )

@router.put("/{room_id}", response_model=Room)
def update_room(
    room_id: int,
    room: RoomBase,
    db: Session = Depends(deps.get_db),
    admin_user: User = Depends(get_admin_user)
):
    db_room = crud.update_room(db, room_id, room)
    if not db_room:
        raise HTTPException(status_code=404, detail="Room not found")
    return Room(
        id=db_room.id,
        room_type=db_room.room_type.value if hasattr(db_room.room_type, 'value') else db_room.room_type,
        capacity=db_room.capacity,
        name=db_room.name
    )

@router.delete("/{room_id}", response_model=Room)
def delete_room(
    room_id: int,
    db: Session = Depends(deps.get_db),
    admin_user: User = Depends(get_admin_user)
):
    db_room = crud.delete_room(db, room_id)
    if not db_room:
        raise HTTPException(status_code=404, detail="Room not found")
    return Room(
        id=db_room.id,
        room_type=db_room.room_type.value if hasattr(db_room.room_type, 'value') else db_room.room_type,
        capacity=db_room.capacity,
        name=db_room.name
    )
