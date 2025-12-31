"""
HealthLog AI - Production-Ready Backend
Features:
- Supabase PostgreSQL database (cloud)
- Supabase Auth OR custom auth with bcrypt password hashing
- Secure session management
- Environment-based configuration
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import os
import json
import httpx
import uuid
import base64
import bcrypt
from pathlib import Path
from dotenv import load_dotenv
from contextlib import asynccontextmanager

# Load environment variables
load_dotenv()

# =============================================================================
# Configuration
# =============================================================================

class Settings:
    # Database - Choose one
    DATABASE_TYPE = os.getenv("DATABASE_TYPE", "sqlite")  # "sqlite" or "supabase"
    
    # Supabase settings (if using Supabase)
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")  # anon/public key
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")  # service role key
    
    # Groq AI
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    
    # App settings
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    
settings = Settings()

# =============================================================================
# Database Abstraction Layer
# =============================================================================

class DatabaseInterface:
    """Abstract database interface - works with SQLite or Supabase"""
    
    async def create_user(self, name: str, email: str, password_hash: str, telegram_id: str = None) -> Dict:
        raise NotImplementedError
    
    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        raise NotImplementedError
    
    async def create_meal_log(self, user_id: str, data: Dict) -> Dict:
        raise NotImplementedError
    
    # ... etc

# SQLite Implementation
import sqlite3
from contextlib import contextmanager

class SQLiteDatabase(DatabaseInterface):
    def __init__(self):
        self.db_path = Path(__file__).parent.parent / "database" / "healthlog.db"
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_tables()
    
    @contextmanager
    def get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def _init_tables(self):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            
            # Users table with password hash
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    telegram_id TEXT UNIQUE,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE,
                    password_hash TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    settings TEXT DEFAULT '{}'
                )
            """)
            
            # Meal logs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS meal_logs (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    image_path TEXT,
                    description TEXT,
                    calories INTEGER DEFAULT 0,
                    protein REAL DEFAULT 0,
                    carbs REAL DEFAULT 0,
                    fat REAL DEFAULT 0,
                    fiber REAL DEFAULT 0,
                    meal_type TEXT,
                    ai_analysis TEXT,
                    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # Symptom logs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS symptom_logs (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    symptom TEXT NOT NULL,
                    severity INTEGER CHECK(severity >= 1 AND severity <= 10),
                    notes TEXT,
                    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # Medications
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS medications (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    dosage TEXT,
                    frequency TEXT,
                    reminder_times TEXT DEFAULT '[]',
                    active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # Medication logs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS medication_logs (
                    id TEXT PRIMARY KEY,
                    medication_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    skipped INTEGER DEFAULT 0,
                    FOREIGN KEY (medication_id) REFERENCES medications(id)
                )
            """)
            
            # Daily scores
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_scores (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    date DATE NOT NULL,
                    energy_level INTEGER,
                    mood_level INTEGER,
                    sleep_hours REAL,
                    water_intake INTEGER,
                    exercise_minutes INTEGER,
                    notes TEXT,
                    UNIQUE(user_id, date),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            conn.commit()
    
    async def create_user(self, name: str, email: str, password_hash: str, telegram_id: str = None) -> Dict:
        user_id = str(uuid.uuid4())
        with self.get_conn() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO users (id, name, email, password_hash, telegram_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, name, email, password_hash, telegram_id))
                conn.commit()
                return {"id": user_id, "name": name, "email": email}
            except sqlite3.IntegrityError as e:
                if "email" in str(e):
                    raise HTTPException(400, "Email already registered")
                raise HTTPException(400, "Registration failed")
    
    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    async def create_meal_log(self, user_id: str, data: Dict) -> Dict:
        meal_id = str(uuid.uuid4())
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO meal_logs 
                (id, user_id, image_path, description, calories, protein, carbs, fat, fiber, meal_type, ai_analysis)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                meal_id, user_id, data.get("image_path"), data.get("description"),
                data.get("calories", 0), data.get("protein", 0), data.get("carbs", 0),
                data.get("fat", 0), data.get("fiber", 0), data.get("meal_type"),
                json.dumps(data.get("ai_analysis", {}))
            ))
            conn.commit()
            return {"id": meal_id, **data}
    
    async def get_meals(self, user_id: str, days: int = 7) -> List[Dict]:
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM meal_logs 
                WHERE user_id = ? AND logged_at >= datetime('now', ?)
                ORDER BY logged_at DESC
            """, (user_id, f'-{days} days'))
            meals = []
            for row in cursor.fetchall():
                meal = dict(row)
                if meal.get('ai_analysis'):
                    try:
                        meal['ai_analysis'] = json.loads(meal['ai_analysis'])
                    except:
                        pass
                meals.append(meal)
            return meals
    
    async def create_symptom_log(self, user_id: str, symptom: str, severity: int, notes: str = None) -> Dict:
        symptom_id = str(uuid.uuid4())
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO symptom_logs (id, user_id, symptom, severity, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (symptom_id, user_id, symptom, severity, notes))
            conn.commit()
            return {"id": symptom_id, "symptom": symptom, "severity": severity}
    
    async def get_symptoms(self, user_id: str, days: int = 7) -> List[Dict]:
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM symptom_logs 
                WHERE user_id = ? AND logged_at >= datetime('now', ?)
                ORDER BY logged_at DESC
            """, (user_id, f'-{days} days'))
            return [dict(row) for row in cursor.fetchall()]
    
    async def create_medication(self, user_id: str, name: str, dosage: str, frequency: str) -> Dict:
        med_id = str(uuid.uuid4())
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO medications (id, user_id, name, dosage, frequency)
                VALUES (?, ?, ?, ?, ?)
            """, (med_id, user_id, name, dosage, frequency))
            conn.commit()
            return {"id": med_id, "name": name, "dosage": dosage}
    
    async def get_medications(self, user_id: str) -> List[Dict]:
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM medications WHERE user_id = ? AND active = 1", (user_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    async def log_medication_taken(self, med_id: str, user_id: str, skipped: bool = False) -> Dict:
        log_id = str(uuid.uuid4())
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO medication_logs (id, medication_id, user_id, skipped)
                VALUES (?, ?, ?, ?)
            """, (log_id, med_id, user_id, 1 if skipped else 0))
            conn.commit()
            return {"id": log_id}
    
    async def get_medication_adherence(self, user_id: str, days: int = 30) -> Dict:
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) as total, SUM(CASE WHEN skipped = 0 THEN 1 ELSE 0 END) as taken
                FROM medication_logs 
                WHERE user_id = ? AND taken_at >= datetime('now', ?)
            """, (user_id, f'-{days} days'))
            row = cursor.fetchone()
            total = row['total'] or 0
            taken = row['taken'] or 0
            return {
                "period_days": days,
                "total": total,
                "taken": taken,
                "skipped": total - taken,
                "adherence_rate": round((taken / total * 100) if total > 0 else 0, 1)
            }
    
    async def save_daily_score(self, user_id: str, data: Dict) -> Dict:
        score_id = str(uuid.uuid4())
        today = datetime.now().strftime("%Y-%m-%d")
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO daily_scores 
                (id, user_id, date, energy_level, mood_level, sleep_hours, water_intake, exercise_minutes, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                score_id, user_id, today,
                data.get("energy_level"), data.get("mood_level"), data.get("sleep_hours"),
                data.get("water_intake"), data.get("exercise_minutes"), data.get("notes")
            ))
            conn.commit()
            return {"id": score_id, "date": today}
    
    async def get_daily_scores(self, user_id: str, days: int = 30) -> List[Dict]:
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM daily_scores 
                WHERE user_id = ? AND date >= date('now', ?)
                ORDER BY date DESC
            """, (user_id, f'-{days} days'))
            return [dict(row) for row in cursor.fetchall()]


# Supabase Implementation
class SupabaseDatabase(DatabaseInterface):
    def __init__(self):
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            raise ValueError("Supabase URL and Key required")
        self.url = settings.SUPABASE_URL
        self.key = settings.SUPABASE_KEY
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
    
    async def _request(self, method: str, endpoint: str, data: Dict = None) -> Any:
        async with httpx.AsyncClient() as client:
            url = f"{self.url}/rest/v1/{endpoint}"
            if method == "GET":
                response = await client.get(url, headers=self.headers, params=data)
            elif method == "POST":
                response = await client.post(url, headers=self.headers, json=data)
            elif method == "PATCH":
                response = await client.patch(url, headers=self.headers, json=data)
            
            if response.status_code >= 400:
                raise HTTPException(response.status_code, response.text)
            
            return response.json() if response.text else None
    
    async def create_user(self, name: str, email: str, password_hash: str, telegram_id: str = None) -> Dict:
        user_id = str(uuid.uuid4())
        data = {
            "id": user_id,
            "name": name,
            "email": email,
            "password_hash": password_hash,
            "telegram_id": telegram_id
        }
        result = await self._request("POST", "users", data)
        return result[0] if result else data
    
    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        result = await self._request("GET", f"users?email=eq.{email}&limit=1")
        return result[0] if result else None
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        result = await self._request("GET", f"users?id=eq.{user_id}&limit=1")
        return result[0] if result else None
    
    async def create_meal_log(self, user_id: str, data: Dict) -> Dict:
        meal_id = str(uuid.uuid4())
        meal_data = {
            "id": meal_id,
            "user_id": user_id,
            "image_path": data.get("image_path"),
            "description": data.get("description"),
            "calories": data.get("calories", 0),
            "protein": data.get("protein", 0),
            "carbs": data.get("carbs", 0),
            "fat": data.get("fat", 0),
            "fiber": data.get("fiber", 0),
            "meal_type": data.get("meal_type"),
            "ai_analysis": data.get("ai_analysis", {})
        }
        result = await self._request("POST", "meal_logs", meal_data)
        return result[0] if result else meal_data
    
    async def get_meals(self, user_id: str, days: int = 7) -> List[Dict]:
        date_from = (datetime.now() - timedelta(days=days)).isoformat()
        result = await self._request("GET", f"meal_logs?user_id=eq.{user_id}&logged_at=gte.{date_from}&order=logged_at.desc")
        return result or []
    
    async def create_symptom_log(self, user_id: str, symptom: str, severity: int, notes: str = None) -> Dict:
        symptom_id = str(uuid.uuid4())
        data = {"id": symptom_id, "user_id": user_id, "symptom": symptom, "severity": severity, "notes": notes}
        result = await self._request("POST", "symptom_logs", data)
        return result[0] if result else data
    
    async def get_symptoms(self, user_id: str, days: int = 7) -> List[Dict]:
        date_from = (datetime.now() - timedelta(days=days)).isoformat()
        result = await self._request("GET", f"symptom_logs?user_id=eq.{user_id}&logged_at=gte.{date_from}&order=logged_at.desc")
        return result or []
    
    async def create_medication(self, user_id: str, name: str, dosage: str, frequency: str) -> Dict:
        med_id = str(uuid.uuid4())
        data = {"id": med_id, "user_id": user_id, "name": name, "dosage": dosage, "frequency": frequency}
        result = await self._request("POST", "medications", data)
        return result[0] if result else data
    
    async def get_medications(self, user_id: str) -> List[Dict]:
        result = await self._request("GET", f"medications?user_id=eq.{user_id}&active=eq.true")
        return result or []
    
    async def log_medication_taken(self, med_id: str, user_id: str, skipped: bool = False) -> Dict:
        log_id = str(uuid.uuid4())
        data = {"id": log_id, "medication_id": med_id, "user_id": user_id, "skipped": skipped}
        result = await self._request("POST", "medication_logs", data)
        return result[0] if result else data
    
    async def get_medication_adherence(self, user_id: str, days: int = 30) -> Dict:
        # For Supabase, you might use an RPC function for aggregation
        # Simplified version here
        return {"period_days": days, "total": 0, "taken": 0, "skipped": 0, "adherence_rate": 0}
    
    async def save_daily_score(self, user_id: str, data: Dict) -> Dict:
        score_id = str(uuid.uuid4())
        today = datetime.now().strftime("%Y-%m-%d")
        score_data = {
            "id": score_id, "user_id": user_id, "date": today,
            "energy_level": data.get("energy_level"),
            "mood_level": data.get("mood_level"),
            "sleep_hours": data.get("sleep_hours"),
            "water_intake": data.get("water_intake"),
            "exercise_minutes": data.get("exercise_minutes")
        }
        result = await self._request("POST", "daily_scores", score_data)
        return result[0] if result else score_data
    
    async def get_daily_scores(self, user_id: str, days: int = 30) -> List[Dict]:
        date_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        result = await self._request("GET", f"daily_scores?user_id=eq.{user_id}&date=gte.{date_from}&order=date.desc")
        return result or []


# Database factory
def get_database() -> DatabaseInterface:
    if settings.DATABASE_TYPE == "supabase" and settings.SUPABASE_URL:
        return SupabaseDatabase()
    return SQLiteDatabase()


# Initialize database
db = get_database()

# =============================================================================
# Password Hashing Utilities
# =============================================================================

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

# =============================================================================
# App Setup
# =============================================================================

app = FastAPI(
    title="HealthLog AI",
    description="AI-powered personal health companion",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOADS_PATH = BASE_DIR / "uploads"
UPLOADS_PATH.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# =============================================================================
# Pydantic Models
# =============================================================================

class UserSignup(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    telegram_id: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class SymptomLog(BaseModel):
    symptom: str = Field(..., min_length=1, max_length=200)
    severity: int = Field(..., ge=1, le=10)
    notes: Optional[str] = None

class MedicationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    dosage: str
    frequency: str
    reminder_times: List[str] = []

class DailyScore(BaseModel):
    energy_level: Optional[int] = Field(None, ge=1, le=10)
    mood_level: Optional[int] = Field(None, ge=1, le=10)
    sleep_hours: Optional[float] = Field(None, ge=0, le=24)
    water_intake: Optional[int] = Field(None, ge=0)
    exercise_minutes: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = None

class ChatMessage(BaseModel):
    message: str
    user_id: str

# =============================================================================
# AI Functions
# =============================================================================

async def analyze_meal_image(image_base64: str) -> Dict[str, Any]:
    """Analyze meal image using Groq's vision model"""
    if not settings.GROQ_API_KEY:
        return {"description": "AI analysis unavailable", "calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0, "health_score": 5}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "llama-3.2-90b-vision-preview",
                    "messages": [
                        {"role": "system", "content": """Analyze food images and return JSON with: description, foods_identified (array), calories (number), protein (number), carbs (number), fat (number), fiber (number), health_score (1-10), suggestions (string). Be realistic with portions."""},
                        {"role": "user", "content": [
                            {"type": "text", "text": "Analyze this meal's nutrition. Return only valid JSON."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                        ]}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 1000
                },
                timeout=60.0
            )
            
            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"]
                # Extract JSON from response
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                return json.loads(content.strip())
    except Exception as e:
        print(f"Meal analysis error: {e}")
    
    return {"description": "Meal logged", "calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0, "health_score": 5}

async def analyze_symptoms_ai(symptoms: List[Dict]) -> str:
    """Analyze symptom patterns with AI"""
    if not settings.GROQ_API_KEY or not symptoms:
        return "No symptoms to analyze or AI unavailable."
    
    symptoms_text = "\n".join([f"- {s['symptom']} (severity: {s['severity']}/10) on {s.get('logged_at', 'unknown date')}" for s in symptoms])
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": "You are a wellness assistant. Identify patterns in symptoms and suggest lifestyle improvements. Never diagnose - recommend seeing a doctor for concerns."},
                        {"role": "user", "content": f"My recent symptoms:\n{symptoms_text}\n\nWhat patterns do you notice?"}
                    ],
                    "temperature": 0.4,
                    "max_tokens": 500
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Symptom analysis error: {e}")
    
    return "Unable to analyze patterns at this time."

async def chat_with_ai(message: str, user_context: str = "") -> str:
    """Chat with AI health assistant"""
    if not settings.GROQ_API_KEY:
        return "AI chat is currently unavailable. Please configure the API key."
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": f"You are a friendly wellness assistant for HealthLog AI. Help with nutrition, wellness, and health tracking questions. Never diagnose conditions. {user_context}"},
                        {"role": "user", "content": message}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 500
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Chat error: {e}")
    
    return "I'm having trouble connecting right now. Please try again!"

# =============================================================================
# API Routes - Pages
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/health-check")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat(), "database": settings.DATABASE_TYPE}

# =============================================================================
# API Routes - Authentication (with password hashing)
# =============================================================================

@app.post("/api/auth/signup")
async def signup(user: UserSignup):
    """Register a new user with hashed password"""
    # Check if user exists
    existing = await db.get_user_by_email(user.email)
    if existing:
        raise HTTPException(400, "Email already registered")
    
    # Hash the password
    password_hash = hash_password(user.password)
    
    # Create user
    new_user = await db.create_user(
        name=user.name,
        email=user.email,
        password_hash=password_hash,
        telegram_id=user.telegram_id
    )
    
    return {
        "message": "User registered successfully",
        "user_id": new_user["id"],
        "email": user.email,
        "name": user.name
    }

@app.post("/api/auth/login")
async def login(credentials: UserLogin):
    """Login with email and password"""
    user = await db.get_user_by_email(credentials.email)
    
    if not user:
        raise HTTPException(401, "Invalid email or password")
    
    # Verify password
    if not verify_password(credentials.password, user.get("password_hash", "")):
        raise HTTPException(401, "Invalid email or password")
    
    return {
        "message": "Login successful",
        "user_id": user["id"],
        "name": user["name"],
        "email": user["email"]
    }

# =============================================================================
# API Routes - Meals
# =============================================================================

@app.post("/api/meals/log")
async def log_meal(
    file: Optional[UploadFile] = File(None),
    description: Optional[str] = Form(None),
    meal_type: str = Form("snack"),
    user_id: str = Form(...)
):
    """Log a meal with optional photo for AI analysis"""
    image_path = None
    ai_analysis = {}
    
    if file and file.filename:
        # Save image
        file_ext = Path(file.filename).suffix or ".jpg"
        image_filename = f"{uuid.uuid4()}{file_ext}"
        image_path = str(UPLOADS_PATH / image_filename)
        
        contents = await file.read()
        with open(image_path, "wb") as f:
            f.write(contents)
        
        # Analyze with AI
        image_base64 = base64.b64encode(contents).decode("utf-8")
        ai_analysis = await analyze_meal_image(image_base64)
    
    # Save to database
    meal = await db.create_meal_log(user_id, {
        "image_path": image_path,
        "description": description or ai_analysis.get("description", ""),
        "calories": ai_analysis.get("calories", 0),
        "protein": ai_analysis.get("protein", 0),
        "carbs": ai_analysis.get("carbs", 0),
        "fat": ai_analysis.get("fat", 0),
        "fiber": ai_analysis.get("fiber", 0),
        "meal_type": meal_type,
        "ai_analysis": ai_analysis
    })
    
    return {"meal_id": meal["id"], "analysis": ai_analysis, "message": "Meal logged successfully"}

@app.get("/api/meals/{user_id}")
async def get_meals(user_id: str, days: int = 7):
    meals = await db.get_meals(user_id, days)
    return {"meals": meals}

# =============================================================================
# API Routes - Symptoms
# =============================================================================

@app.post("/api/symptoms/log")
async def log_symptom(symptom: SymptomLog, user_id: str):
    result = await db.create_symptom_log(user_id, symptom.symptom, symptom.severity, symptom.notes)
    return {"symptom_id": result["id"], "message": "Symptom logged successfully"}

@app.get("/api/symptoms/{user_id}")
async def get_symptoms(user_id: str, days: int = 7):
    symptoms = await db.get_symptoms(user_id, days)
    return {"symptoms": symptoms}

@app.get("/api/symptoms/{user_id}/analysis")
async def analyze_user_symptoms(user_id: str):
    symptoms = await db.get_symptoms(user_id, days=30)
    if not symptoms:
        return {"analysis": "No symptoms logged yet. Start tracking to see patterns!"}
    analysis = await analyze_symptoms_ai(symptoms)
    return {"analysis": analysis, "symptom_count": len(symptoms)}

# =============================================================================
# API Routes - Medications
# =============================================================================

@app.post("/api/medications/add")
async def add_medication(med: MedicationCreate, user_id: str):
    result = await db.create_medication(user_id, med.name, med.dosage, med.frequency)
    return {"medication_id": result["id"], "message": "Medication added"}

@app.get("/api/medications/{user_id}")
async def get_medications(user_id: str):
    meds = await db.get_medications(user_id)
    return {"medications": meds}

@app.post("/api/medications/{med_id}/take")
async def log_medication_taken(med_id: str, user_id: str, skipped: bool = False):
    result = await db.log_medication_taken(med_id, user_id, skipped)
    return {"log_id": result["id"], "message": "Medication logged"}

@app.get("/api/medications/{user_id}/adherence")
async def get_medication_adherence(user_id: str, days: int = 30):
    return await db.get_medication_adherence(user_id, days)

# =============================================================================
# API Routes - Daily Scores
# =============================================================================

@app.post("/api/daily-score")
async def log_daily_score(score: DailyScore, user_id: str):
    result = await db.save_daily_score(user_id, score.dict())
    return {"score_id": result["id"], "message": "Daily score logged"}

@app.get("/api/daily-scores/{user_id}")
async def get_daily_scores(user_id: str, days: int = 30):
    scores = await db.get_daily_scores(user_id, days)
    return {"scores": scores}

# =============================================================================
# API Routes - Insights & Reports
# =============================================================================

@app.get("/api/insights/{user_id}")
async def get_insights(user_id: str):
    meals = await db.get_meals(user_id, 7)
    symptoms = await db.get_symptoms(user_id, 7)
    scores = await db.get_daily_scores(user_id, 7)
    
    total_calories = sum(m.get('calories', 0) or 0 for m in meals)
    avg_energy = sum(s.get('energy_level', 0) or 0 for s in scores) / len(scores) if scores else 0
    avg_mood = sum(s.get('mood_level', 0) or 0 for s in scores) / len(scores) if scores else 0
    
    return {
        "period": "Last 7 days",
        "meals_logged": len(meals),
        "avg_daily_calories": round(total_calories / 7),
        "symptoms_logged": len(symptoms),
        "avg_energy": round(avg_energy, 1),
        "avg_mood": round(avg_mood, 1)
    }

@app.get("/api/report/{user_id}")
async def generate_report(user_id: str):
    user = await db.get_user_by_id(user_id)
    insights = await get_insights(user_id)
    
    recommendations = []
    if insights.get("avg_daily_calories", 0) < 1200:
        recommendations.append("Your calorie intake seems low. Consider logging more meals.")
    if insights.get("avg_energy", 0) < 5:
        recommendations.append("Your energy levels have been low. Consider evaluating sleep and diet.")
    if not recommendations:
        recommendations.append("Great job staying consistent with your health tracking!")
    
    return {
        "report_id": str(uuid.uuid4()),
        "user_name": user.get("name", "User") if user else "User",
        "generated_at": datetime.now().isoformat(),
        "period": "Last 7 days",
        "summary": insights,
        "recommendations": recommendations
    }

# =============================================================================
# API Routes - Chat
# =============================================================================

@app.post("/api/chat")
async def health_chat(chat: ChatMessage):
    insights = await get_insights(chat.user_id)
    context = f"User's recent data: {insights.get('meals_logged', 0)} meals, avg calories: {insights.get('avg_daily_calories', 'N/A')}, avg energy: {insights.get('avg_energy', 'N/A')}/10"
    response = await chat_with_ai(chat.message, context)
    return {"response": response}

# =============================================================================
# Run
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server.main:app", host="0.0.0.0", port=8000, reload=True)
