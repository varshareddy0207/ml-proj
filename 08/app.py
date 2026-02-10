import streamlit as st
from logic import recommend_from_input

# ------------------ Page Config ------------------
st.set_page_config(
    page_title="Athlete Nutrition & Fitness Recommender",
    page_icon="🏋️",
    layout="centered"
)

st.title("🏋️ Athlete Nutrition & Fitness Recommender")
st.caption("Personalized nutrition, hydration & training guidance")

st.markdown("---")

# ------------------ Input Section ------------------
st.header("👤 Enter Athlete Details")

col1, col2 = st.columns(2)

with col1:
    sex = st.selectbox("Sex", ["Male", "Female"])
    age = st.number_input("Age", min_value=10, max_value=100, value=25)
    height_cm = st.number_input("Height (cm)", min_value=100, max_value=250, value=175)

with col2:
    weight_kg = st.number_input("Weight (kg)", min_value=30, max_value=200, value=70)
    sport = st.text_input("Sport", "Soccer")
    activity_level = st.selectbox("Activity Level", ["Low", "Medium", "High"])

activity_map = {"Low": 1, "Medium": 2, "High": 3}
activity_level_num = activity_map[activity_level]

st.markdown("---")

# ------------------ Button ------------------
if st.button("🚀 Get My Fitness Plan"):
    try:
        result = recommend_from_input(
            sex,
            height_cm,
            weight_kg,
            age,
            sport,
            activity_level_num
        )

        st.success("✅ Your personalized fitness plan is ready!")

        # ---- Read nested outputs ----
        profile = result["Profile Summary"]
        daily = result["Daily Needs"]

        # ------------------ Summary Cards ------------------
        st.subheader("📌 Fitness Summary")

        c1, c2, c3 = st.columns(3)
        c1.metric("Sport", profile["Sport"])
        c2.metric("BMI", profile["BMI"])
        c3.metric("Athlete Type", profile["Athlete Type"])

        st.markdown("---")

        # ------------------ Daily Needs ------------------
        st.subheader("🔥 Daily Requirements")

        d1, d2 = st.columns(2)
        d1.info(f"🍽️ Calories Needed: **{daily['Calories']}**")
        d2.info(f"💧 Hydration: **{daily['Hydration']}**")

        # ------------------ Training ------------------
        st.subheader("🏃 Training Recommendation")
        st.write(f"➡️ {result['Training Recommendation']}")

        # ------------------ Injury Guidance ------------------
        st.subheader("🩹 Injury Risk & Safety")
        st.info(result["Injury Risk"])

        # ------------------ Nutrition Plan ------------------
        st.subheader("🍽️ Recommended Foods")
        st.caption("Foods selected based on your calorie needs and fitness profile")
        st.dataframe(result["Nutrition Plan"], use_container_width=True)

    except Exception as e:
        st.error(f"⚠️ Something went wrong: {e}")
