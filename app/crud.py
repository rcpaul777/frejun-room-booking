from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import date, time, datetime
from typing import List, Optional
import models, schemas, security
from fastapi import HTTPException, status

# User CRUD

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_team(db: Session, team_id: int):
    return db.query(models.Team).filter(models.Team.id == team_id).first()

def get_room(db: Session, room_id: int):
    return db.query(models.Room).filter(models.Room.id == room_id).first()

def get_rooms_by_type(db: Session, room_type: str):
    return db.query(models.Room).filter(models.Room.room_type == room_type).all()

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()

def authenticate_user(db: Session, email: str, password: str) -> Optional[models.User]:
    user = get_user_by_email(db, email=email)
    if not user:
        return None
    if not security.verify_password(password, user.hashed_password):
        return None
    return user

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    hashed_password = security.get_password_hash(user.password)
    db_user = models.User(
        name=user.name,
        email=user.email,
        hashed_password=hashed_password,
        age=user.age,
        gender=user.gender,
        is_admin=user.is_admin,
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_team(db: Session, team: schemas.TeamCreate):
    db_team = models.Team(name=team.name)
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    # Add members
    for user_id in team.member_ids:
        user = get_user(db, user_id)
        if user:
            db_team.members.append(user)
    db.commit()
    db.refresh(db_team)
    return db_team

# Booking CRUD

def create_booking(db: Session, booking: schemas.BookingCreate):
    # Prevent double booking for user/team
    if booking.user_id:
        existing = db.query(models.Booking).filter(
            models.Booking.user_id == booking.user_id,
            models.Booking.slot_date == booking.slot_date,
            models.Booking.slot_start < booking.slot_end,
            models.Booking.slot_end > booking.slot_start,
            models.Booking.is_active == True
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="User already has a booking for this slot.")
    if booking.team_id:
        existing = db.query(models.Booking).filter(
            models.Booking.team_id == booking.team_id,
            models.Booking.slot_date == booking.slot_date,
            models.Booking.slot_start < booking.slot_end,
            models.Booking.slot_end > booking.slot_start,
            models.Booking.is_active == True
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Team already has a booking for this slot.")

    # Room allocation logic
    rooms = get_rooms_by_type(db, booking.room_type)
    if not rooms:
        raise HTTPException(status_code=404, detail="No rooms of this type exist.")
    # Find available room
    available_rooms = get_available_rooms(db, booking.slot_date, booking.slot_start, booking.slot_end, booking.room_type)
    if not available_rooms:
        raise HTTPException(status_code=400, detail="No available room for the selected slot and type.")
    # Shared desk: assign to desk with <4 users
    if booking.room_type == "shared":
        for room in available_rooms:
            # Count current bookings for this desk/slot
            count = db.query(models.Booking).filter(
                models.Booking.room_id == room.id,
                models.Booking.slot_date == booking.slot_date,
                models.Booking.slot_start < booking.slot_end,
                models.Booking.slot_end > booking.slot_start,
                models.Booking.is_active == True
            ).count()
            if count < room.capacity:
                db_booking = models.Booking(
                    room_id=room.id,
                    user_id=booking.user_id,
                    team_id=None,
                    slot_date=booking.slot_date,
                    slot_start=booking.slot_start,
                    slot_end=booking.slot_end,
                    is_active=True
                )
                db.add(db_booking)
                db.commit()
                db.refresh(db_booking)
                return db_booking
        raise HTTPException(status_code=400, detail="No available shared desk for the selected slot.")
    # Conference: team only, team size >= 3
    elif booking.room_type == "conference":
        if not booking.team_id:
            raise HTTPException(status_code=400, detail="Conference room requires a team.")
        team = get_team(db, booking.team_id)
        if not team or len(team.members) < 3:
            raise HTTPException(status_code=400, detail="Conference room requires a team of at least 3 members.")
        # Children <10 included in headcount
        db_booking = models.Booking(
            room_id=available_rooms[0].id,
            user_id=None,
            team_id=booking.team_id,
            slot_date=booking.slot_date,
            slot_start=booking.slot_start,
            slot_end=booking.slot_end,
            is_active=True
        )
        db.add(db_booking)
        db.commit()
        db.refresh(db_booking)
        return db_booking
    # Private: single user only
    elif booking.room_type == "private":
        if not booking.user_id:
            raise HTTPException(status_code=400, detail="Private room requires a user.")
        db_booking = models.Booking(
            room_id=available_rooms[0].id,
            user_id=booking.user_id,
            team_id=None,
            slot_date=booking.slot_date,
            slot_start=booking.slot_start,
            slot_end=booking.slot_end,
            is_active=True
        )
        db.add(db_booking)
        db.commit()
        db.refresh(db_booking)
        return db_booking
    else:
        raise HTTPException(status_code=400, detail="Invalid room type.")

def get_bookings(db: Session, skip: int = 0, limit: int = 100, user_id: int = None, team_id: int = None):
    q = db.query(models.Booking).filter(models.Booking.is_active == True)
    if user_id:
        q = q.filter(models.Booking.user_id == user_id)
    if team_id:
        q = q.filter(models.Booking.team_id == team_id)
    return q.offset(skip).limit(limit).all()

def cancel_booking(db: Session, booking_id: int):
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id, models.Booking.is_active == True).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")
    booking.is_active = False
    db.commit()
    db.refresh(booking)
    return booking

def get_available_rooms(db: Session, slot_date: date, slot_start: time, slot_end: time, room_type: str):
    # Get all rooms of type
    rooms = get_rooms_by_type(db, room_type)
    available = []
    for room in rooms:
        # For shared, check if < capacity
        if room_type == "shared":
            count = db.query(models.Booking).filter(
                models.Booking.room_id == room.id,
                models.Booking.slot_date == slot_date,
                models.Booking.slot_start < slot_end,
                models.Booking.slot_end > slot_start,
                models.Booking.is_active == True
            ).count()
            if count < room.capacity:
                available.append(room)
        else:
            overlap = db.query(models.Booking).filter(
                models.Booking.room_id == room.id,
                models.Booking.slot_date == slot_date,
                models.Booking.slot_start < slot_end,
                models.Booking.slot_end > slot_start,
                models.Booking.is_active == True
            ).count()
            if overlap == 0:
                available.append(room)
    return available

def get_all_rooms(db: Session):
    return db.query(models.Room).all()

def create_room(db: Session, room: schemas.RoomBase):
    db_room = models.Room(
        room_type=room.room_type,
        capacity=room.capacity,
        name=room.name
    )
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room

def update_room(db: Session, room_id: int, room: schemas.RoomBase):
    db_room = get_room(db, room_id)
    if not db_room:
        raise HTTPException(status_code=404, detail="Room not found.")
    db_room.room_type = room.room_type
    db_room.capacity = room.capacity
    db_room.name = room.name
    db.commit()
    db.refresh(db_room)
    return db_room

def delete_room(db: Session, room_id: int):
    db_room = get_room(db, room_id)
    if not db_room:
        raise HTTPException(status_code=404, detail="Room not found.")
    db.delete(db_room)
    db.commit()
    return db_room

def get_user_bookings(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Booking).filter(models.Booking.user_id == user_id, models.Booking.is_active == True).offset(skip).limit(limit).all()

def get_overlapping_bookings(db: Session, room_id: int, slot_date: date, slot_start: time, slot_end: time):
    return db.query(models.Booking).filter(
        models.Booking.room_id == room_id,
        models.Booking.slot_date == slot_date,
        models.Booking.slot_start < slot_end,
        models.Booking.slot_end > slot_start,
        models.Booking.is_active == True
    ).all()

def get_booking(db: Session, booking_id: int):
    return db.query(models.Booking).filter(models.Booking.id == booking_id).first()
