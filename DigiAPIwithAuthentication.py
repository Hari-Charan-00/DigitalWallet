#here we have updated the exisiting code with an extra feature called TOKEN
#We need to create a user first, login with the user, then have to request the APIs with the token

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt

app = FastAPI()

# Add CORS middleware to allow connections from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_NAME = 'expenses.db'
SECRET_KEY = "supersecretkey"  # Use environment variables in production!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# ---------- Models ----------
class User(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int  # seconds till access token expiry
    token_type: str = "bearer"

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class Expense(BaseModel):
    id: Optional[int] = None
    title: str
    amount: float
    category: str
    description: str
    date: Optional[str] = None

# ---------- DB Setup ----------
def setup_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        amount REAL NOT NULL,
        category TEXT,
        description TEXT,
        date TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_tokens (
        user_id INTEGER PRIMARY KEY,
        access_token TEXT NOT NULL,
        refresh_token TEXT NOT NULL,
        access_token_expiry INTEGER NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')
    conn.commit()
    conn.close()

setup_database()

# ... keep existing code (auth utilities functions)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token, expire

def decode_token(token: str):
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = decode_token(token)
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

def get_user_id(username: str) -> int:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]
    raise HTTPException(status_code=404, detail="User not found")

# ---------- Auth Endpoints ----------
@app.post("/register")
def register(user: User):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                       (user.username, hash_password(user.password)))
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists")
    finally:
        conn.close()
    return {"msg": "User registered successfully"}

@app.post("/login", response_model=Token)
def login(user: User):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Verify user credentials
    cursor.execute("SELECT id, password FROM users WHERE username = ?", (user.username,))
    row = cursor.fetchone()
    if row is None or not verify_password(user.password, row[1]):
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user_id = row[0]

    # Check if there's an unexpired access token for this user in DB
    cursor.execute("SELECT access_token, refresh_token, access_token_expiry FROM user_tokens WHERE user_id = ?", (user_id,))
    token_row = cursor.fetchone()

    now_ts = int(datetime.utcnow().timestamp())

    if token_row:
        access_token_db, refresh_token_db, access_token_expiry = token_row
        if access_token_expiry > now_ts:
            # Return existing tokens with remaining expiry
            conn.close()
            expires_in = access_token_expiry - now_ts
            return Token(
                access_token=access_token_db,
                refresh_token=refresh_token_db,
                expires_in=expires_in,
                token_type="bearer"
            )
        else:
            # Tokens expired, remove old tokens
            cursor.execute("DELETE FROM user_tokens WHERE user_id = ?", (user_id,))
            conn.commit()

    # Create new tokens
    access_token, access_expiry_dt = create_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token, _ = create_token(
        data={"sub": user.username, "type": "refresh"},
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    access_expiry_ts = int(access_expiry_dt.timestamp())

    # Store tokens in DB
    cursor.execute('''
        INSERT OR REPLACE INTO user_tokens (user_id, access_token, refresh_token, access_token_expiry)
        VALUES (?, ?, ?, ?)
    ''', (user_id, access_token, refresh_token, access_expiry_ts))
    conn.commit()
    conn.close()

    expires_in = access_expiry_ts - now_ts
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
        token_type="bearer"
    )

@app.post("/refresh", response_model=Token)
def refresh_token(token_request: TokenRefreshRequest):
    try:
        payload = decode_token(token_request.refresh_token)
        username = payload.get("sub")
        token_type = payload.get("type")
        if token_type != "refresh" or username is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user_id = get_user_id(username)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Verify refresh token matches stored one
    cursor.execute("SELECT refresh_token FROM user_tokens WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row or row[0] != token_request.refresh_token:
        conn.close()
        raise HTTPException(status_code=401, detail="Refresh token mismatch")

    # Create new access token
    access_token, access_expiry_dt = create_token(
        data={"sub": username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    access_expiry_ts = int(access_expiry_dt.timestamp())

    # Update DB
    cursor.execute('''
        UPDATE user_tokens SET access_token = ?, access_token_expiry = ? WHERE user_id = ?
    ''', (access_token, access_expiry_ts, user_id))
    conn.commit()
    conn.close()

    now_ts = int(datetime.utcnow().timestamp())
    expires_in = access_expiry_ts - now_ts

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
        token_type="bearer"
    )

# ---------- Expense Endpoints ----------
@app.get("/expenses/", response_model=List[Expense])
def list_expenses(current_user: str = Depends(get_current_user)):
    user_id = get_user_id(current_user)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, title, amount, category, description, date FROM expenses WHERE user_id = ? ORDER BY date DESC",
        (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [Expense(id=row[0], title=row[1], amount=row[2], category=row[3], description=row[4], date=row[5]) for row in rows]

@app.post("/expenses/", response_model=Expense)
def add_expense(expense: Expense, current_user: str = Depends(get_current_user)):
    user_id = get_user_id(current_user)
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO expenses (user_id, title, amount, category, description, date)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, expense.title, expense.amount, expense.category, expense.description, now))
    conn.commit()
    expense_id = cursor.lastrowid
    conn.close()
    return Expense(id=expense_id, title=expense.title, amount=expense.amount,
                   category=expense.category, description=expense.description, date=now)

@app.put("/expenses/{expense_id}", response_model=Expense)
def update_expense(expense_id: int, expense: Expense, current_user: str = Depends(get_current_user)):
    user_id = get_user_id(current_user)
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE expenses
        SET title = ?, amount = ?, category = ?, description = ?, date = ?
        WHERE id = ? AND user_id = ?
    ''', (expense.title, expense.amount, expense.category, expense.description, now, expense_id, user_id))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Expense not found or unauthorized")
    conn.commit()
    conn.close()
    return Expense(id=expense_id, title=expense.title, amount=expense.amount,
                   category=expense.category, description=expense.description, date=now)

@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: int, current_user: str = Depends(get_current_user)):
    user_id = get_user_id(current_user)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE id = ? AND user_id = ?", (expense_id, user_id))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Expense not found or unauthorized")
    conn.commit()
    conn.close()
    return {"detail": "Expense deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    print("Starting server on http://localhost:9000")
    uvicorn.run(app, host="0.0.0.0", port=9000)
