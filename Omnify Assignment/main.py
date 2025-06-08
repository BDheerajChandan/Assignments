from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
from zoneinfo import ZoneInfo
import uuid
import json
import logging
import os
import threading

app = FastAPI()

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- File paths for persistence ---
CLASSES_FILE = "classes_data.json"
BOOKINGS_FILE = "bookings_data.json"

# --- Thread lock for booking concurrency safety ---
booking_lock = threading.Lock()

# --- Models ---
class FitnessClass(BaseModel):
    id: str
    name: str
    instructor: str
    datetime: datetime
    timezone: str
    available_slots: int

class FitnessClassResponse(BaseModel):
    id: str
    name: str
    instructor: str
    datetime: str  # ISO formatted datetime string in requested timezone
    available_slots: int

class BookingRequest(BaseModel):
    class_id: str
    client_name: str
    client_email: EmailStr

class Booking(BaseModel):
    booking_id: str
    class_id: str
    class_name: str
    client_name: str
    client_email: EmailStr
    class_time: datetime

# --- In-memory data stores ---
classes: List[FitnessClass] = []
bookings: List[Booking] = []

def save_classes_to_file():
    """Save current classes list to JSON file with UTF-8 encoding"""
    with open(CLASSES_FILE, "w", encoding="utf-8") as f:
        json.dump([cls.dict() for cls in classes], f, default=str)
    logging.info("Saved classes data to file.")

def save_bookings_to_file():
    """Save current bookings list to JSON file with UTF-8 encoding"""
    with open(BOOKINGS_FILE, "w", encoding="utf-8") as f:
        json.dump([b.dict() for b in bookings], f, default=str)
    logging.info("Saved bookings data to file.")

def load_classes_from_file():
    """Load classes from file or seed defaults if file missing"""
    global classes
    if os.path.exists(CLASSES_FILE):
        with open(CLASSES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            classes = [FitnessClass(**item) for item in data]
            logging.info("Loaded classes data from file.")
    else:
        seed_data()
        save_classes_to_file()

def load_bookings_from_file():
    """Load bookings from file or initialize empty list"""
    global bookings
    if os.path.exists(BOOKINGS_FILE):
        with open(BOOKINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            bookings = [Booking(**item) for item in data]
            logging.info("Loaded bookings data from file.")
    else:
        bookings = []

def seed_data():
    """Seed initial fitness classes"""
    global classes
    classes = [
        FitnessClass(
            id=str(uuid.uuid4()),
            name="Yoga",
            instructor="Alice",
            datetime=datetime(2025, 6, 9, 7, 0, tzinfo=ZoneInfo("Asia/Kolkata")),
            timezone="Asia/Kolkata",
            available_slots=5
        ),
        FitnessClass(
            id=str(uuid.uuid4()),
            name="Zumba",
            instructor="Bob",
            datetime=datetime(2025, 6, 9, 9, 0, tzinfo=ZoneInfo("Asia/Kolkata")),
            timezone="Asia/Kolkata",
            available_slots=5
        ),
        FitnessClass(
            id=str(uuid.uuid4()),
            name="HIIT",
            instructor="Charlie",
            datetime=datetime(2025, 6, 10, 18, 0, tzinfo=ZoneInfo("Asia/Kolkata")),
            timezone="Asia/Kolkata",
            available_slots=3
        )
    ]
    logging.info("Seeded initial classes data.")

# Load data on startup
load_classes_from_file()
load_bookings_from_file()

# --- API Endpoints ---

@app.get("/classes", response_model=List[FitnessClassResponse])
def get_classes(timezone: Optional[str] = Query("Asia/Kolkata")):
    """
    Get all upcoming fitness classes adjusted to requested timezone.
    """
    try:
        user_zone = ZoneInfo(timezone)
    except Exception:
        logging.error(f"Invalid timezone requested: {timezone}")
        raise HTTPException(status_code=400, detail="Invalid timezone")

    result = []
    for cls in classes:
        local_time = cls.datetime.astimezone(user_zone)
        result.append(FitnessClassResponse(
            id=cls.id,
            name=cls.name,
            instructor=cls.instructor,
            datetime=local_time.isoformat(),
            available_slots=cls.available_slots
        ))

    logging.info(f"Returned {len(result)} classes for timezone {timezone}")
    return result

@app.post("/book")
def book_class(request: BookingRequest):
    """
    Book a spot in a fitness class if slots are available.
    Thread-safe booking with lock to prevent race conditions.
    """
    with booking_lock:
        cls = next((c for c in classes if c.id == request.class_id), None)
        if not cls:
            logging.warning(f"Booking failed: Class ID {request.class_id} not found.")
            raise HTTPException(status_code=404, detail="Class not found")

        if cls.available_slots <= 0:
            logging.warning(f"Booking failed: No available slots for class {cls.name}")
            raise HTTPException(status_code=400, detail="No available slots")

        # Decrease available slot
        cls.available_slots -= 1
        save_classes_to_file()  # persist change

        booking = Booking(
            booking_id=str(uuid.uuid4()),
            class_id=cls.id,
            class_name=cls.name,
            client_name=request.client_name,
            client_email=request.client_email,
            class_time=cls.datetime
        )
        bookings.append(booking)
        save_bookings_to_file()  # persist new booking

        logging.info(f"Booking successful: {booking.booking_id} for class {cls.name}")
        return {"message": "Booking successful", "booking_id": booking.booking_id}

@app.get("/bookings", response_model=List[Booking])
def get_bookings(email: EmailStr):
    """
    Retrieve all bookings made by a specific email address.
    """
    result = [b for b in bookings if b.client_email == email]
    logging.info(f"Returned {len(result)} bookings for email {email}")
    return result
