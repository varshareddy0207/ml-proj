import sqlite3
import hashlib
import json
from datetime import datetime, timedelta

# ------------------ Database Connection ------------------
def create_connection():
    return sqlite3.connect("athlete.db", check_same_thread=False)

# ------------------ Security ------------------
def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# ------------------ Create Tables ------------------
def create_tables():
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS athletes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            Email TEXT,
            password TEXT,
            age INTEGER,
            sex TEXT,
            height REAL,
            weight REAL,
            sport TEXT,
            activity_level TEXT,
            goal TEXT DEFAULT 'General Fitness',
            plan TEXT,
            weekly_workout TEXT,
            meal_plan TEXT,
            meal_date TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            athlete_id INTEGER,
            date TEXT,
            calories INTEGER,
            hydration REAL,
            workout_done INTEGER,
            workout_duration INTEGER,
            sleep_hours REAL DEFAULT 0,
            stress_level TEXT DEFAULT 'Medium'
        )
    """)

    conn.commit()
    conn.close()

# ------------------ Account ------------------
def create_account(username, Email, password, age, sex, height, weight, sport, activity_level, goal):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM athletes WHERE name=?", (username,))
    if cursor.fetchone():
        conn.close()
        return False

    hashed_pw = hash_password(password)

    cursor.execute("""
        INSERT INTO athletes (name, Email, password, age, sex, height, weight, sport, activity_level, goal)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (username, Email, hashed_pw, age, sex, height, weight, sport, activity_level, goal))

    conn.commit()
    conn.close()
    return True

def login_user(name, password):
    conn = create_connection()
    cursor = conn.cursor()

    hashed_pw = hash_password(password)
    cursor.execute("SELECT id FROM athletes WHERE name=? AND password=?", (name, hashed_pw))
    result = cursor.fetchone()

    conn.close()
    return result[0] if result else None

# ------------------ Streak ------------------
def get_user_streak(athlete_id):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT date FROM daily_logs WHERE athlete_id=? ORDER BY date DESC", (athlete_id,))
    dates = [datetime.strptime(row[0], "%Y-%m-%d").date() for row in cursor.fetchall()]

    conn.close()

    if not dates:
        return 0

    streak = 0
    today = datetime.now().date()

    if dates[0] < today - timedelta(days=1):
        return 0

    for i in range(len(dates)):
        if dates[i] == today - timedelta(days=streak):
            streak += 1
        else:
            break

    return streak

# ------------------ Profile ------------------
def get_athlete_profile(athlete_id):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT age, sex, height, weight, sport, activity_level, goal
        FROM athletes WHERE id=?
    """, (athlete_id,))

    row = cursor.fetchone()
    conn.close()

    return {
        "age": row[0],
        "sex": row[1],
        "height": row[2],
        "weight": row[3],
        "sport": row[4],
        "activity_level": row[5],
        "goal": row[6]
    }

# ------------------ Plan ------------------
def save_plan(user_id, plan):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE athletes SET plan=? WHERE id=?",
        (json.dumps(plan), user_id)
    )

    conn.commit()
    conn.close()

def get_saved_plan(user_id):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT plan FROM athletes WHERE id=?", (user_id,))
    result = cursor.fetchone()

    conn.close()

    if result and result[0]:
        return json.loads(result[0])
    return None

# ------------------ Weekly Workout ------------------
def save_week_plan(user_id, plan):
    conn = create_connection()
    cursor = conn.cursor()

    data = {
        "week": datetime.now().isocalendar()[1],
        "plan": plan
    }

    cursor.execute(
        "UPDATE athletes SET weekly_workout=? WHERE id=?",
        (json.dumps(data), user_id)
    )

    conn.commit()
    conn.close()

def get_week_plan(user_id):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT weekly_workout FROM athletes WHERE id=?", (user_id,))
    result = cursor.fetchone()

    conn.close()

    if result and result[0]:
        data = json.loads(result[0])
        if data["week"] == datetime.now().isocalendar()[1]:
            return data["plan"]

    return None

# ------------------ Logs ------------------
def log_daily_progress(athlete_id, date, calories, hydration, workout_done, workout_duration, sleep, stress):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO daily_logs (athlete_id, date, calories, hydration, workout_done, workout_duration, sleep_hours, stress_level)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (athlete_id, date, calories, hydration, workout_done, workout_duration, sleep, stress))

    conn.commit()
    conn.close()

def get_logs_by_athlete(athlete_id):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT date, calories, hydration, workout_done, workout_duration, sleep_hours,stress_level
        FROM daily_logs WHERE athlete_id=? ORDER BY date DESC
    """, (athlete_id,))

    rows = cursor.fetchall()
    conn.close()
    return rows
def save_meal_plan(user_id, meal_plan):
    conn = create_connection()
    cursor = conn.cursor()

    today = datetime.now().strftime("%Y-%m-%d")

    cursor.execute("""
        UPDATE athletes 
        SET meal_plan=?, meal_date=? 
        WHERE id=?
    """, (json.dumps(meal_plan), today, user_id))

    conn.commit()
    conn.close()
def get_meal_plan(user_id):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT meal_plan, meal_date FROM athletes WHERE id=?", (user_id,))
    result = cursor.fetchone()

    conn.close()

    today = datetime.now().strftime("%Y-%m-%d")

    if result and result[0] and result[1] == today:
        return json.loads(result[0])   # ✅ SAME DAY → reuse

    return None  # ❌ generate new
def update_profile(user_id, age, height, weight, activity_level):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE athletes
        SET age=?, height=?, weight=?, activity_level=?
        WHERE id=?
    """, (age, height, weight, activity_level, user_id))

    conn.commit()
    conn.close()