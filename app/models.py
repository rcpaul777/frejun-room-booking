from sqlalchemy import Column, Integer, String, ForeignKey, Date, Time, Enum, Boolean, Table
from sqlalchemy.orm import relationship
from sqlalchemy.types import DateTime
from sqlalchemy.sql import func
from database import Base
import enum

class GenderEnum(enum.Enum):
    male = "male"
    female = "female"
    other = "other"

class RoomTypeEnum(enum.Enum):
    private = "private"
    conference = "conference"
    shared = "shared"

team_members = Table(
    "team_members",
    Base.metadata,
    Column("team_id", Integer, ForeignKey("teams.id")),
    Column("user_id", Integer, ForeignKey("users.id"))
)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(Enum(GenderEnum), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    members = relationship("User", secondary=team_members)

class Room(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key=True, index=True)
    room_type = Column(Enum(RoomTypeEnum), nullable=False)
    capacity = Column(Integer, nullable=False)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)

    bookings = relationship("Booking", back_populates="room")

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    slot_date = Column(Date, nullable=False)
    slot_start = Column(Time, nullable=False)
    slot_end = Column(Time, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

    room = relationship("Room")
    user = relationship("User")
    team = relationship("Team")
