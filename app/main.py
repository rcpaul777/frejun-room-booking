from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

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

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Create tables and include routers
Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(bookings.router)
app.include_router(rooms.router)
