from datetime import date, time, datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, validator

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: Optional[str] = None

class UserBase(BaseModel):
    name: str
    email: EmailStr
    age: int
    gender: str
    is_admin: bool = False

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: str
    @validator("created_at", pre=True)
    def parse_created_at(cls, value):
        if isinstance(value, datetime):
            return value.isoformat()
        return value
    class Config:
        from_attributes = True

class TeamBase(BaseModel):
    name: str

class TeamCreate(TeamBase):
    member_ids: List[int]

class Team(TeamBase):
    id: int
    members: List['UserResponse']
    class Config:
        from_attributes = True

class RoomBase(BaseModel):
    room_type: str
    capacity: int
    name: str

class Room(RoomBase):
    id: int
    class Config:
        orm_mode = True

class BookingBase(BaseModel):
    slot_date: date
    slot_start: time
    slot_end: time

class BookingCreate(BookingBase):
    room_type: str
    user_id: Optional[int] = None
    team_id: Optional[int] = None

class Booking(BookingBase):
    id: int
    room_id: int
    user_id: Optional[int] = None
    team_id: Optional[int] = None
    is_active: bool
    class Config:
        from_attributes = True
