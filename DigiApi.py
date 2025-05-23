from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import sqlite3
from datetime import datetime

app = FastAPI()

DB_NAME = 'expenses.db'

# Pydantic model for request/response validation
class Expense(BaseModel):
    id: int = None
    amount: float
    category: str
    description: str
    date: str = None

def setup_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL,
            category TEXT,
            description TEXT,
            date TEXT
        )
    ''')
    conn.commit()
    conn.close()

setup_database()

@app.get("/expenses/", response_model=List[Expense])
def list_expenses():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, amount, category, description, date FROM expenses ORDER BY date DESC")
    rows = cursor.fetchall()
    conn.close()
    expenses = [Expense(id=row[0], amount=row[1], category=row[2], description=row[3], date=row[4]) for row in rows]
    return expenses

@app.post("/expenses/", response_model=Expense)
def add_expense(expense: Expense):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO expenses (amount, category, description, date)
        VALUES (?, ?, ?, ?)
    ''', (expense.amount, expense.category, expense.description, now))
    conn.commit()
    expense_id = cursor.lastrowid
    conn.close()
    return Expense(id=expense_id, amount=expense.amount, category=expense.category, description=expense.description, date=now)

@app.put("/expenses/{expense_id}", response_model=Expense)
def update_expense(expense_id: int, expense: Expense):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        UPDATE expenses
        SET amount = ?, category = ?, description = ?, date = ?
        WHERE id = ?
    ''', (expense.amount, expense.category, expense.description, now, expense_id))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Expense not found")
    conn.commit()
    conn.close()
    return Expense(id=expense_id, amount=expense.amount, category=expense.category, description=expense.description, date=now)

@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Expense not found")
    conn.commit()
    conn.close()
    return {"detail": "Expense deleted successfully"}

