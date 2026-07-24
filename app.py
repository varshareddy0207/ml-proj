import streamlit as st
import pandas as pd
from openai import OpenAI

# ✅ MUST BE FIRST
st.set_page_config(
    page_title="Smart Fitness & Health Tracker",
    layout="wide"
)

# ------------------ OPENAI ------------------

# ------------------ CHATBOT FUNCTION ------------------
def get_bot_response(user_input, plan):

    workout_info = ""
    diet_info = ""

    if plan:
        workout_info = str(plan.get("Workout Plan", ""))
        diet_info = str(plan.get("diet", ""))

    prompt = f"""
    You are an AI fitness and nutrition assistant.

    User current workout plan:
    {workout_info}

    User current diet plan:
    {diet_info}

    Your job:
    - Explain workouts step-by-step
    - Explain workout form correctly
    - Explain recipes simply
    - Suggest healthy cooking methods
    - Keep answers beginner friendly
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_input}
        ]
    )

    return response.choices[0].message.content


# ------------------ Imports ------------------
from datetime import date
from logic import calculate_bmi
from logic import calorie_needs
from logic import predict_weight_change
from logic import water_needs
from database import get_meal_plan, save_meal_plan
from logic import generate_meal_plan
from database import update_profile

from database import (
    create_tables, create_account, login_user,
    log_daily_progress, get_logs_by_athlete,
    get_athlete_profile, get_user_streak,
    save_plan, get_saved_plan
)

from logic import recommend_from_input

# ------------------ INIT ------------------
create_tables()

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "plan" not in st.session_state:
    st.session_state.plan = None

# ------------------ GLOBAL STYLE ------------------
st.markdown("""<style>
.stApp { background: linear-gradient(135deg, #F3F0FF, #E6E9FF); }
.center-text { text-align: center; }

.stButton > button {
    background: linear-gradient(135deg, #6C63FF, #8B85FF);
    color: white;
    border-radius: 12px;
    padding: 10px 24px;
    margin: 12px auto;
    display: block;
    transition: 0.3s;
}
.stButton > button:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 25px rgba(108,99,255,0.35);
}
</style>""", unsafe_allow_html=True)

# ================== HOME ==================
if "user_id" not in st.session_state:
    st.session_state.user_id = None

if not st.session_state.user_id:

    st.markdown("<h1 class='center-text'>🏋️ Smart Fitness & Health Tracker</h1>", unsafe_allow_html=True)
    st.markdown("<h4 class='center-text'>Your Personal AI Fitness Coach</h4>", unsafe_allow_html=True)
    st.markdown("<p class='center-text'>Track • Improve • Transform</p>", unsafe_allow_html=True)

    # ---------- BUTTONS ----------
    col1, col2, col3 = st.columns([1,1,1])

    with col2:
        b1, b2 = st.columns(2)

        with b1:
            if st.button("Login"):
                st.session_state.page = "login"

        with b2:
            if st.button("Sign Up"):
                st.session_state.page = "signup"

    # ---------- CENTER FORM ----------
    center_col = st.columns([1,2,1])[1]

    with center_col:

        # -------- LOGIN FORM --------
        if st.session_state.get("page") == "login":

            st.subheader("Login")

            username = st.text_input("Username")
            password = st.text_input("Password", type="password")

            if st.button("Login Now"):

                user_id = login_user(username, password)

                if user_id:
                    st.session_state.user_id = user_id
                    st.success("Login successful")
                    st.rerun()
                else:
                    st.error("Invalid credentials")

        # -------- SIGNUP FORM --------
        elif st.session_state.get("page") == "signup":

            st.subheader("Sign Up")

            with st.form("signup_form"):

                name = st.text_input("Username")
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")

                age = st.number_input("Age", 10, 100)
                height = st.number_input("Height (cm)", 100.0, 250.0)
                weight = st.number_input("Weight (kg)", 30.0, 200.0)

                sex = st.selectbox("Sex", ["Male", "Female"])
                activity = st.selectbox("Activity Level", ["Low", "Medium", "High"])
                goal = st.selectbox("Goal", ["General Fitness", "Weight Loss", "Muscle Gain", "Athlete"])

                sport = st.text_input("Sport") if goal == "Athlete" else ""

                submit = st.form_submit_button("Create Account")

                if submit:

                    success = create_account(
                        name, email, password, age, sex,
                        height, weight, sport, activity, goal
                    )

                    if success:
                        st.success("Account created! Now login.")
                        st.session_state.page = "login"
                        st.rerun()
                    else:
                        st.error("Username exists")

# ================== DASHBOARD ==================
else:

    st.sidebar.title("Dashboard")

    streak = get_user_streak(st.session_state.user_id)
    st.sidebar.metric("Streak", f"{streak} Days")

    # ✅ CHATBOT ADDED HERE
    page = st.sidebar.radio(
        "Navigate",
        ["Profile", "Plan", "Logs", "Progress", "Chatbot"]
    )

    if st.sidebar.button("Logout"):
        st.session_state.user_id = None
        st.session_state.plan = None
        st.rerun()

    profile_data = get_athlete_profile(st.session_state.user_id)

    # ================= PROFILE =================
    if page == "Profile":

        st.subheader("👤 Profile Settings")

        profile = get_athlete_profile(st.session_state.user_id)

        col1, col2 = st.columns(2)

        with col1:
            age = st.number_input("Age", 10, 80, value=profile["age"])
            height = st.number_input("Height (cm)", value=profile["height"])
            weight = st.number_input("Weight (kg)", value=profile["weight"])

        with col2:
            activity = st.selectbox(
                "Activity Level",
                ["Low", "Moderate", "High"],
                index=["Low", "Moderate", "High"].index(profile["activity_level"])
            )

        if st.button("💾 Update Profile"):

            update_profile(
                st.session_state.user_id,
                age,
                height,
                weight,
                activity
            )

            st.success("Profile updated successfully ✅")

        bmi = calculate_bmi(weight, height)

        st.metric("BMI", bmi)

        if bmi < 18.5:
            status = "Underweight"
        elif bmi < 25:
            status = "Normal"
        elif bmi < 30:
            status = "Overweight"
        else:
            status = "Obese"

        st.write(f"Status: {status}")

        calories = calorie_needs(weight, activity)
        water = water_needs(weight)

        st.markdown("### 📊 Health Metrics")

        c1, c2, c3 = st.columns(3)

        c1.metric("BMI", bmi)
        c2.metric("Calories/day", f"{int(calories)} kcal")
        c3.metric("Water/day", f"{water} L")

    # ================= PLAN =================
    elif page == "Plan":

        st.header("Your Plan")

        food_type = st.selectbox("Diet Type", ["Indian", "Western"])

        if st.button("Generate Plan"):

            activity_map = {"Low":1,"Medium":2,"High":3}

            plan = recommend_from_input(
                profile_data["sex"],
                float(profile_data["height"]),
                float(profile_data["weight"]),
                int(profile_data["age"]),
                profile_data["sport"],
                activity_map[profile_data["activity_level"]],
                profile_data["goal"],
                food_type,
                st.session_state.user_id
            )

            st.session_state.plan = plan

            save_plan(st.session_state.user_id, plan)

            meal_plan = get_meal_plan(st.session_state.user_id)

            if meal_plan is None:
                meal_plan = generate_meal_plan(profile_data["goal"], food_type)
                save_meal_plan(st.session_state.user_id, meal_plan)

            st.subheader("Meal Plan")

            for meal in meal_plan:
                st.write(f"**{meal['Meal']}**: {meal['Food']}")

        if st.session_state.plan:

            result = st.session_state.plan

            st.subheader(f"{result['today']} - {result['focus']}")

            st.metric("Calories", result["calories"])

            st.subheader("Workout")

            for w in result["Workout Plan"]:
                st.write(f"{w['exercise']} - {w['body_part']}")

        else:
            st.info("Generate a plan first")

    # ================= LOGS =================
    elif page == "Logs":

        st.markdown("## Daily Activity Tracker")

        st.markdown("""
        <style>
        .card {
            padding: 20px;
            border-radius: 15px;
            background-color: #f5f7fa;
            margin-bottom: 15px;
            box-shadow: 0px 4px 10px rgba(0,0,0,0.05);
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            log_date = st.date_input("Date", value=date.today())
            calories = st.number_input("Calories", 0)
            water = st.number_input("Water (L)", 0.0)

        with col2:
            sleep = st.number_input("Sleep (hrs)", 0.0)
            gym = st.selectbox("🏋️ Gym?", ["No", "Yes"])

            workout_time = 0

            if gym == "Yes":
                workout_time = st.number_input("⏱ Workout (min)", 0)

            stress = st.selectbox("Stress Level", ["Low", "Medium", "High"])

        st.markdown('</div>', unsafe_allow_html=True)

        col1,col2,col3 = st.columns([1,1,1])

        with col2:

            if st.button("Save Log", use_container_width=True):

                log_daily_progress(
                    st.session_state.user_id,
                    str(log_date),
                    calories,
                    water,
                    1 if gym == "Yes" else 0,
                    workout_time,
                    sleep,
                    stress
                )

                st.success("Saved successfully")

    # ================= PROGRESS =================
    elif page == "Progress":

        import plotly.express as px

        st.title("📊 Your Fitness Dashboard")

        logs = get_logs_by_athlete(st.session_state.user_id)

        if logs:

            df = pd.DataFrame(logs, columns=[
                "date","calories","hydration","workout_done",
                "workout_duration","sleep","stress"
            ])

            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date")

            st.line_chart(df[["calories", "hydration", "sleep"]])

        else:
            st.info("No progress data yet. Start logging daily!")

    # ================= CHATBOT =================
    elif page == "Chatbot":

        st.title("💬 AI Fitness Assistant")

        st.write("Ask about workouts, exercise form, recipes, cooking tips, and nutrition.")

        # ---------------- CHAT HISTORY ----------------
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:

            with st.chat_message(message["role"]):
                st.write(message["content"])

        # ---------------- USER INPUT ----------------
        user_input = st.chat_input(
            "Ask about workouts or cooking..."
        )

        if user_input:

            # USER MESSAGE
            st.session_state.messages.append({
                "role": "user",
                "content": user_input
            })

            with st.chat_message("user"):
                st.write(user_input)

            # BOT RESPONSE
            with st.spinner("Thinking..."):

                bot_reply = get_bot_response(
                    user_input,
                    st.session_state.plan
                )

            # DISPLAY BOT RESPONSE
            with st.chat_message("assistant"):
                st.write(bot_reply)

            # SAVE MESSAGE
            st.session_state.messages.append({
                "role": "assistant",
                "content": bot_reply
            })