from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from fastapi import Form, Query
from starlette.middleware.sessions import SessionMiddleware
import crud, schemas, security, models
from sqlalchemy.orm import Session as OrmSession
from deps import get_db
from fastapi import Depends

from database import Base, engine
from routers import bookings, rooms, auth

app = FastAPI(
    title="FreJun Room Booking API",
    description="Virtual Workspace Room Booking System",
    version="1.0.0",
    openapi_tags=[
        {
            "name": "authentication",
            "description": "Operations with user authentication"
        },
        {
            "name": "bookings",
            "description": "Room booking operations"
        },
        {
            "name": "rooms",
            "description": "Room management operations"
        }
    ]
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, you may want to restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.add_middleware(SessionMiddleware, secret_key="supersecretkey")

# Helper to get current user from session
async def get_current_user_from_session(request: Request, db: OrmSession = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    user = crud.get_user(db, user_id)
    return user

@app.get("/")
def root(request: Request, db: OrmSession = Depends(get_db)):
    user_id = request.session.get("user_id")
    if user_id:
        return RedirectResponse("/dashboard", status_code=302)
    # Always show login page at root if not logged in
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/login")
def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login_post(request: Request, db: OrmSession = Depends(get_db), email: str = Form(...), password: str = Form(...)):
    user = crud.authenticate_user(db, email=email, password=password)
    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})
    request.session["user_id"] = user.id
    return RedirectResponse("/dashboard", status_code=302)

@app.get("/signup")
def signup_get(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/signup")
def signup_post(request: Request, db: OrmSession = Depends(get_db), name: str = Form(...), email: str = Form(...), password: str = Form(...), age: int = Form(...), gender: str = Form(...)):
    if crud.get_user_by_email(db, email=email):
        return templates.TemplateResponse("signup.html", {"request": request, "error": "Email already registered"})
    user = crud.create_user(db, schemas.UserCreate(name=name, email=email, password=password, age=age, gender=gender, is_admin=False))
    request.session["user_id"] = user.id
    return RedirectResponse("/dashboard", status_code=302)

@app.get("/dashboard")
def dashboard(request: Request, db: OrmSession = Depends(get_db), page: int = Query(1, ge=1)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/login")
    user = crud.get_user(db, user_id)
    page_size = 10
    bookings = crud.get_user_bookings(db, user_id, skip=(page-1)*page_size, limit=page_size)
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user, "bookings": bookings, "page": page})

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login")

@app.post("/book")
def book_room(request: Request, db: OrmSession = Depends(get_db), room_type: str = Form(...), slot_date: str = Form(...), slot_start: str = Form(...), slot_end: str = Form(...), user_id: int = Form(None)):
    session_user_id = request.session.get("user_id")
    if not session_user_id:
        return RedirectResponse("/login")
    user = crud.get_user(db, session_user_id)
    # Admin can book for others
    booking_user_id = user_id if (user.is_admin and user_id) else session_user_id
    booking_in = schemas.BookingCreate(
        user_id=booking_user_id,
        room_type=room_type,
        slot_date=slot_date,
        slot_start=slot_start,
        slot_end=slot_end
    )
    try:
        crud.create_booking(db, booking_in)
        success = "Room booked successfully!"
        bookings = crud.get_user_bookings(db, session_user_id)
        return templates.TemplateResponse("dashboard.html", {"request": request, "user": user, "bookings": bookings, "success": success})
    except Exception as e:
        bookings = crud.get_user_bookings(db, session_user_id)
        return templates.TemplateResponse("dashboard.html", {"request": request, "user": user, "bookings": bookings, "error": str(e)})

@app.post("/cancel")
def cancel_booking(request: Request, db: OrmSession = Depends(get_db), booking_id: int = Form(...)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/login")
    try:
        crud.cancel_booking(db, booking_id)
        success = "Booking cancelled successfully."
    except Exception as e:
        success = None
        error = str(e)
    user = crud.get_user(db, user_id)
    bookings = crud.get_user_bookings(db, user_id)
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user, "bookings": bookings, "success": success if success else None, "error": error if not success else None})

@app.post("/change-password")
def change_password(request: Request, db: OrmSession = Depends(get_db), current_password: str = Form(...), new_password: str = Form(...), confirm_password: str = Form(...)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/login")
    user = crud.get_user(db, user_id)
    bookings = crud.get_user_bookings(db, user_id)
    # Validate current password
    if not security.verify_password(current_password, user.hashed_password):
        return templates.TemplateResponse("dashboard.html", {"request": request, "user": user, "bookings": bookings, "error": "Current password is incorrect."})
    # Validate new password match
    if new_password != confirm_password:
        return templates.TemplateResponse("dashboard.html", {"request": request, "user": user, "bookings": bookings, "error": "New passwords do not match."})
    # Optionally: enforce password policy here
    # Update password
    user.hashed_password = security.get_password_hash(new_password)
    db.commit()
    db.refresh(user)
    success = "Password changed successfully."
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user, "bookings": bookings, "success": success})

# Create tables and include routers
Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(bookings.router)
app.include_router(rooms.router)
