from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import date, time
import models, schemas, security

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_team(db: Session, team_id: int):
    return db.query(models.Team).filter(models.Team.id == team_id).first()

def get_room(db: Session, room_id: int):
    return db.query(models.Room).filter(models.Room.id == room_id).first()

def get_rooms_by_type(db: Session, room_type: str):
    return db.query(models.Room).filter(models.Room.room_type == room_type).all()

def get_user_by_email(db: Session, email: str) -> models.User:
    return db.query(models.User).filter(models.User.email == email).first()

def authenticate_user(db: Session, email: str, password: str) -> models.User:
    user = get_user_by_email(db, email=email)
    if not user:
        return None
    if not security.verify_password(password, user.hashed_password):
        return None
    return user

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    hashed_password = security.get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        name=user.name,
        age=user.age,
        gender=user.gender,
        is_admin=user.is_admin
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
    # Add members by email (assuming team.members is a list of emails)
    missing_users = []
    for email in getattr(team, 'members', []):
        user = get_user_by_email(db, email)
        if user:
            db_team.members.append(user)
        else:
            missing_users.append(email)
    db.commit()
    db.refresh(db_team)
    if missing_users:
        # Optionally, raise or log missing users
        pass
    return db_team

from fastapi import HTTPException
from datetime import datetime

def create_booking(db: Session, booking: schemas.BookingCreate):
    # Validate slot times
    if booking.slot_start >= booking.slot_end:
        raise Exception("Slot start time must be before end time")
    # Validate booking is not in the past
    today = date.today()
    now = datetime.now().time()
    if booking.slot_date < today or (booking.slot_date == today and booking.slot_end <= now):
        raise Exception("Cannot book a slot in the past")
    # Check if user exists
    user = get_user(db, booking.user_id) if hasattr(booking, 'user_id') else None
    if not user:
        raise Exception("User not found")
    # Check if room exists
    room = get_room(db, booking.room_id) if hasattr(booking, 'room_id') else None
    if not room:
        raise Exception("Room not found")
    # Prevent user double-booking (same slot, any room)
    user_overlaps = db.query(models.Booking).filter(
        models.Booking.user_id == user.id,
        models.Booking.slot_date == booking.slot_date,
        models.Booking.slot_start < booking.slot_end,
        models.Booking.slot_end > booking.slot_start,
        models.Booking.is_active == True
    ).all()
    if user_overlaps:
        raise Exception("User already has a booking for this slot")
    # Check for overlapping bookings in the room
    overlaps = get_overlapping_bookings(db, room.id, booking.slot_date, booking.slot_start, booking.slot_end)
    if room.room_type == 'shared':
        if len(overlaps) >= room.capacity:
            raise Exception("Shared room is at full capacity for this slot")
    else:
        if overlaps:
            raise Exception("Room is already booked for this slot")
    # TODO: Add team booking and children logic as per business rules
    # Create booking
    db_booking = models.Booking(
        room_id=room.id,
        user_id=user.id,
        slot_date=booking.slot_date,
        slot_start=booking.slot_start,
        slot_end=booking.slot_end,
        is_active=True
    )
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking

def get_bookings(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Booking).filter(models.Booking.is_active == True).offset(skip).limit(limit).all()

def cancel_booking(db: Session, booking_id: int):
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id, models.Booking.is_active == True).first()
    if booking:
        booking.is_active = False
        db.commit()
        db.refresh(booking)
    return booking

def get_available_rooms(db: Session, slot_date: date, slot_start: time, slot_end: time, room_type: str):
    # Returns available rooms for the slot and type
    booked_room_ids = db.query(models.Booking.room_id).filter(
        models.Booking.slot_date == slot_date,
        models.Booking.slot_start < slot_end,
        models.Booking.slot_end > slot_start,
        models.Booking.is_active == True
    ).subquery()
    return db.query(models.Room).filter(
        models.Room.room_type == room_type,
        ~models.Room.id.in_(booked_room_ids)
    ).all()

def get_all_rooms(db: Session):
    """Get all rooms"""
    return db.query(models.Room).all()

def create_room(db: Session, room: schemas.RoomBase):
    """Create a new room"""
    db_room = models.Room(**room.dict())
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room

def update_room(db: Session, room_id: int, room: schemas.RoomBase):
    """Update a room"""
    db_room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not db_room:
        return None
    
    for key, value in room.dict().items():
        setattr(db_room, key, value)
    
    db.commit()
    db.refresh(db_room)
    return db_room

def delete_room(db: Session, room_id: int):
    """Delete a room"""
    db_room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not db_room:
        return None
    
    db.delete(db_room)
    db.commit()
    return db_room

def get_user_bookings(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """Get bookings for a specific user"""
    return db.query(models.Booking)\
        .filter(models.Booking.user_id == user_id, models.Booking.is_active == True)\
        .offset(skip)\
        .limit(limit)\
        .all()

def get_overlapping_bookings(db: Session, room_id: int, slot_date: date, slot_start: time, slot_end: time):
    """Get all active bookings that overlap with the given time slot for a room"""
    return db.query(models.Booking).filter(
        models.Booking.room_id == room_id,
        models.Booking.slot_date == slot_date,
        models.Booking.slot_start < slot_end,
        models.Booking.slot_end > slot_start,
        models.Booking.is_active == True
    ).all()

def get_booking(db: Session, booking_id: int):
    """Get a booking by ID"""
    return db.query(models.Booking).filter(
        models.Booking.id == booking_id,
        models.Booking.is_active == True
    ).first()
