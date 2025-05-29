# frejun-room-booking
Virtual Workspace Room Booking System - FreJun Take-Home Challenge

## Setup Instructions

1. **Clone the repository** and navigate to the project directory.

2. **Build and start the services:**
   ```bash
   docker-compose up --build
   ```

3. **Initialize the rooms in the database:**
   Open a new terminal and run:
   ```bash
   docker-compose exec api python app/init_db.py
   ```

4. **Access the API documentation:**
   Open your browser at [http://localhost:8000/docs](http://localhost:8000/docs)

5. **Try the API:**
   - Create users and teams (see API docs for endpoints)
   - Book, cancel, and check available rooms

6. **Run tests:**
   ```bash
   docker-compose exec api pytest
   ```

## Assumptions
- Private rooms: 1 user per room per slot
- Conference rooms: Teams of 3+ (children <10 included in headcount, not in seat count)
- Shared desks: Up to 4 users per desk per slot (children <10 do not occupy a seat)
- A user/team can book only one slot at a time
- Overlapping slots are blocked for the same room
- All business rules from the challenge are enforced

## API Endpoints
- `POST /api/v1/bookings/` — Book a room
- `POST /api/v1/bookings/cancel/{booking_id}/` — Cancel a booking
- `GET /api/v1/bookings/` — View current bookings (paginated)
- `GET /api/v1/rooms/available/` — Check room availability per slot

## Bonus Features
- **Swagger/OpenAPI docs**: Available at `/docs`
- **Pagination**: Supported on `/api/v1/bookings/`
- **Tests**: Run with `pytest`

## Verification Steps (Layperson Guide)
1. Start the app and DB with Docker Compose
2. Initialize rooms
3. Open [http://localhost:8000/docs](http://localhost:8000/docs)
4. Use the interactive docs to create users, teams, and bookings
5. Try booking/cancelling and check room availability
6. Run tests to verify correctness

---
For any issues, please check the logs or contact the developer.
