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
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db.close()
            return True
        except OperationalError:
            print("Database not ready, waiting...")
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
        else:
            # Check if rooms exist
            existing_rooms = db.query(Room).first()
            if existing_rooms:
                print("Rooms already exist in database. Skipping initialization.")
                return

        # Private Rooms (1-person offices)
        private_rooms = [
            {"name": "Executive-1", "capacity": 1, "type": RoomTypeEnum.private, "description": "Corner office with window"},
            {"name": "Executive-2", "capacity": 1, "type": RoomTypeEnum.private, "description": "Corner office with window"},
            {"name": "Private-1", "capacity": 1, "type": RoomTypeEnum.private, "description": "Standard private office"},
            {"name": "Private-2", "capacity": 1, "type": RoomTypeEnum.private, "description": "Standard private office"},
            {"name": "Private-3", "capacity": 1, "type": RoomTypeEnum.private, "description": "Standard private office"},
            {"name": "Private-4", "capacity": 1, "type": RoomTypeEnum.private, "description": "Standard private office"},
            {"name": "Focus-1", "capacity": 1, "type": RoomTypeEnum.private, "description": "Quiet focus room"},
            {"name": "Focus-2", "capacity": 1, "type": RoomTypeEnum.private, "description": "Quiet focus room"},
        ]

        # Conference Rooms
        conference_rooms = [
            {"name": "BoardRoom", "capacity": 20, "type": RoomTypeEnum.conference, "description": "Main boardroom with video conferencing"},
            {"name": "MeetingRoom-A", "capacity": 12, "type": RoomTypeEnum.conference, "description": "Medium meeting room with whiteboard"},
            {"name": "MeetingRoom-B", "capacity": 8, "type": RoomTypeEnum.conference, "description": "Small meeting room with display"},
            {"name": "BrainstormRoom", "capacity": 6, "type": RoomTypeEnum.conference, "description": "Creative space with writable walls"},
        ]

        # Shared Spaces
        shared_spaces = [
            {"name": "CollabZone-1", "capacity": 4, "type": RoomTypeEnum.shared, "description": "Open collaboration space with whiteboards"},
            {"name": "CollabZone-2", "capacity": 4, "type": RoomTypeEnum.shared, "description": "Open collaboration space with display"},
            {"name": "QuietZone", "capacity": 4, "type": RoomTypeEnum.shared, "description": "Quiet working space"},
        ]

        # Add all rooms to database
        print("Initializing rooms in database...")
        for room_data in private_rooms + conference_rooms + shared_spaces:
            room = Room(
                name=room_data["name"],
                room_type=room_data["type"],
                capacity=room_data["capacity"],
                description=room_data["description"]
            )
            db.add(room)

        db.commit()
        print("Rooms initialized successfully!")

    except Exception as e:
        print(f"Error initializing rooms: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("Starting database initialization...")
    wait_for_db()
    init_db()
    init_rooms(clear_existing=True)
    print("Database initialization completed!")
