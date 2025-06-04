import time
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker
from database import SessionLocal, engine
from models import Room, RoomTypeEnum, Base

def wait_for_db(max_retries=30, retry_interval=1):
    """Wait for the database to be ready"""
    for _ in range(max_retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except OperationalError:
            time.sleep(retry_interval)
    raise Exception("Could not connect to database")

def init_db():
    """Create database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

def init_rooms(clear_existing: bool = True):
    """Initialize rooms with detailed configurations"""
    db = SessionLocal()
    
    try:
        # Clear existing rooms if requested
        if clear_existing:
            print("Clearing existing rooms...")
            db.query(Room).delete()
            db.commit()

        # 8 Private Rooms
        for i in range(1, 9):
            room = Room(
                room_type=RoomTypeEnum.private,
                capacity=1,
                name=f"Private Room {i}",
                description="1-person private office"
            )
            db.add(room)

        # 4 Conference Rooms
        for i in range(1, 5):
            room = Room(
                room_type=RoomTypeEnum.conference,
                capacity=10,
                name=f"Conference Room {i}",
                description="Conference room (up to 10 people, children included in headcount)"
            )
            db.add(room)

        # 3 Shared Desks (4 users each)
        for i in range(1, 4):
            room = Room(
                room_type=RoomTypeEnum.shared,
                capacity=4,
                name=f"Shared Desk {i}",
                description="Shared desk (up to 4 users, children <10 do not occupy a seat)"
            )
            db.add(room)

        db.commit()
        print("Rooms initialized successfully!")

    except Exception as e:
        print(f"Error initializing rooms: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Starting database initialization...")
    wait_for_db()
    init_db()
    init_rooms(clear_existing=True)
    print("Database initialization completed!")
