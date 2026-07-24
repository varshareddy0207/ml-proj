import pandas as pd
import joblib
import random
from datetime import datetime

# 🔥 ADD THIS
from database import get_week_plan, save_week_plan

# ------------------ Load ML models ------------------
kmeans = joblib.load("kmeans.pkl")
scaler = joblib.load("scaler.pkl")
sport_encoder = joblib.load("sport_encoder.pkl")

# ------------------ Load Nutrition Dataset ------------------
nutrition_df = pd.read_csv(r"C:\Users\somva\Desktop\08\nutrients_csvfile.csv")

nutrition_df = nutrition_df[[
    "Food", "Calories", "Protein", "Fat", "Carbs", "Fiber"
]]

nutrition_df = nutrition_df.rename(columns={
    "Food": "food_name",
    "Calories": "calories",
    "Protein": "protein",
    "Fat": "fats",
    "Carbs": "carbs",
    "Fiber": "fiber"
})

for col in ["calories", "protein", "carbs", "fats", "fiber"]:
    nutrition_df[col] = pd.to_numeric(nutrition_df[col], errors="coerce")

nutrition_df = nutrition_df.dropna()
nutrition_df = nutrition_df[nutrition_df["calories"] > 0]

# ------------------ Load Indian Food Dataset ------------------
indian_df = pd.read_csv(r"C:\Users\somva\Desktop\08\indian_food.csv")

indian_df = indian_df.rename(columns={
    "name": "food_name",
    "diet": "diet",
    "course": "course"
})

indian_df = indian_df.dropna(subset=["food_name"])

# ------------------ Load Workout Dataset ------------------
workout_df = pd.read_csv(r"C:\Users\somva\Desktop\08\megaGymDataset.csv")

workout_df = workout_df.rename(columns={
    "Title": "exercise",
    "Desc": "description",
    "Type": "type",
    "BodyPart": "body_part",
    "Equipment": "equipment",
    "Level": "difficulty"
})

workout_df = workout_df.dropna()

# ------------------ Helper Functions ------------------

def get_food_by_goal(df, goal, nutrient, min_value):
    if goal == "Weight Loss":
        filtered = df[(df["calories"] < 250) & (df[nutrient] >= min_value)]
    elif goal == "Muscle Gain":
        filtered = df[df["protein"] > 15]
    else:
        filtered = df[df[nutrient] >= min_value]

    if filtered.empty:
        filtered = df

    return filtered.sample(1)


def get_indian_food(course_type, diet_type=None):
    df = indian_df[indian_df["course"].str.contains(course_type, case=False, na=False)]

    if diet_type:
        df = df[df["diet"].str.contains(diet_type, case=False, na=False)]

    if df.empty:
        df = indian_df

    return df.sample(1)["food_name"].values[0]


# ------------------ FIXED WEEKLY PLAN (NO REPEAT) ------------------

def generate_week_plan(df):

    week_days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]

    body_parts = df["body_part"].dropna().unique().tolist()
    random.shuffle(body_parts)

    used_exercises = set()
    weekly_plan = {}

    for i, day in enumerate(week_days):

        focus = body_parts[i % len(body_parts)]

        available = df[df["body_part"] == focus]

        # ❌ Remove already used exercises
        available = available[~available["exercise"].isin(used_exercises)]

        if available.empty:
            available = df[df["body_part"] == focus]

        selected = available.sample(4)

        used_exercises.update(selected["exercise"].tolist())

        weekly_plan[day] = {
            "focus": focus,
            "exercises": selected[["exercise", "description"]].to_dict(orient="records")
        }

    weekly_plan["Sunday"] = {
        "focus": "Rest",
        "exercises": []
    }

    return weekly_plan


def get_today_workout(df, focus):
    filtered = df[df["body_part"].str.contains(focus, case=False, na=False)]

    if filtered.empty:
        filtered = df

    return filtered.sample(4)


# ------------------ Progress Prediction ------------------

def predict_weight_change(current_weight, target_daily_calories, tdee):
    daily_diff = target_daily_calories - tdee
    monthly_change_kg = (daily_diff * 30) / 7700
    return round(current_weight + monthly_change_kg, 2)
def calculate_bmi(weight, height_cm):
    height_m = height_cm / 100
    return round(weight / (height_m ** 2), 2)

def calorie_needs(weight, activity):
    if activity == "Low":
        return weight * 25
    elif activity == "Moderate":
        return weight * 30
    else:
        return weight * 35

def water_needs(weight):
    return round(weight * 0.035, 2)  # liters

def generate_meal_plan(goal, food_type):

    if food_type == "Indian":
        return [
            {"Meal": "Breakfast", "Food": get_indian_food("breakfast")},
            {"Meal": "Lunch", "Food": get_indian_food("main course")},
            {"Meal": "Snack", "Food": get_indian_food("dessert")},
            {"Meal": "Dinner", "Food": get_indian_food("main course")}
        ]

    else:
        return [
            {"Meal": "Breakfast", "Food": get_food_by_goal(nutrition_df, goal, "protein", 10).iloc[0]["food_name"]},
            {"Meal": "Lunch", "Food": get_food_by_goal(nutrition_df, goal, "carbs", 20).iloc[0]["food_name"]},
            {"Meal": "Snack", "Food": nutrition_df.sample(1).iloc[0]["food_name"]},
            {"Meal": "Dinner", "Food": get_food_by_goal(nutrition_df, goal, "protein", 10).iloc[0]["food_name"]}
        ]
# ------------------ MAIN FUNCTION ------------------

def recommend_from_input(sex, height_cm, weight_kg, age, sport, activity_level, goal, food_type, user_id):

    # ---------------- 1. BMR ----------------
    if sex == "Male":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

    activity_map = {1: 1.2, 2: 1.55, 3: 1.9}
    tdee = bmr * activity_map.get(activity_level, 1.2)

    calories = tdee

    # ---------------- 2. Goal ----------------
    if goal == "Weight Loss":
        calories -= 500
        protein = weight_kg * 2.2
    elif goal == "Muscle Gain":
        calories += 300
        protein = weight_kg * 1.8
    elif goal == "Athlete":
        calories += 500
        protein = weight_kg * 2.0
    else:
        protein = weight_kg * 1.5

    fats = (calories * 0.25) / 9
    carbs = (calories - (protein * 4 + fats * 9)) / 4

    # ---------------- 3. WEEK PLAN FIX ----------------
    weekly_plan = get_week_plan(user_id)

    if weekly_plan is None:
        weekly_plan = generate_week_plan(workout_df)
        save_week_plan(user_id, weekly_plan)

    today = datetime.now().strftime("%A")
    today_data = weekly_plan[today]
    today_focus = today_data["focus"]

    # ---------------- 4. WORKOUT ----------------
    if today_focus == "Rest":
        workout_list = [{
            "exercise": "Rest Day",
            "body_part": "Recovery",
            "description": "Take rest and allow muscles to recover."
        }]
    else:
        workout_list = [
            {
                "exercise": ex["exercise"],
                "body_part": today_focus,
                "description": ex["description"]
            }
            for ex in today_data["exercises"]
        ]

    # ---------------- 5. FOOD ----------------
    
    # ---------------- 6. Prediction ----------------
    predicted_weight = predict_weight_change(weight_kg, calories, tdee)

    return {
        "today": today,
        "focus": today_focus,
        "calories": round(calories),
        "Protein (g)": round(protein),
        "Carbs (g)": round(carbs),
        "Fats (g)": round(fats),
        "Predicted Weight (30 days)": predicted_weight,
        "Workout Plan": workout_list,
        
    }