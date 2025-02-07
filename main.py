from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import sqlite3
import datetime

app = FastAPI()

# Подключение к базе данных
conn = sqlite3.connect("car_wash.db", check_same_thread=False)
cursor = conn.cursor()

# Создание таблицы бронирований, если её нет
cursor.execute("""
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT,
    phone TEXT,
    datetime TEXT UNIQUE,
    status TEXT DEFAULT 'booked'
)
""")
conn.commit()

# Модель данных для бронирования
class BookingRequest(BaseModel):
    customer_name: str
    phone: str
    datetime: str  # Формат "YYYY-MM-DD HH:MM"

# Функция для получения свободных слотов
def get_available_slots():
    now = datetime.datetime.now()
    slots = []
    for i in range(1, 8):  # Ближайшие 7 дней
        for hour in range(9, 19):  # Рабочие часы 9:00 - 18:00
            slot = (now + datetime.timedelta(days=i)).replace(hour=hour, minute=0, second=0, microsecond=0)
            cursor.execute("SELECT * FROM bookings WHERE datetime = ?", (slot.strftime("%Y-%m-%d %H:%M"),))
            if not cursor.fetchone():
                slots.append(slot.strftime("%Y-%m-%d %H:%M"))
    return slots

# Получение списка свободных слотов
@app.get("/available_slots", response_model=List[str])
def available_slots():
    return get_available_slots()

# Запись на мойку
@app.post("/book")
def book_slot(booking: BookingRequest):
    try:
        cursor.execute("INSERT INTO bookings (customer_name, phone, datetime) VALUES (?, ?, ?)", 
                       (booking.customer_name, booking.phone, booking.datetime))
        conn.commit()
        return {"message": "Вы успешно записались!"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Это время уже занято")

# Получение всех записей (для администратора)
@app.get("/bookings")
def get_bookings():
    cursor.execute("SELECT * FROM bookings")
    return cursor.fetchall()

# Отмена записи (администратор)
@app.delete("/cancel/{booking_id}")
def cancel_booking(booking_id: int):
    cursor.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
    conn.commit()
    return {"message": "Запись отменена"}
