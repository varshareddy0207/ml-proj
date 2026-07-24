import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import joblib

# ------------------ Load dataset ------------------
df = pd.read_csv(r"C:\Users\somva\Downloads\calories.csv")

# ------------------ Rename columns ------------------
df = df.rename(columns={
    'Gender': 'sex',
    'Age': 'age',
    'Height': 'height_cm',
    'Weight': 'weight_kg',
    'Calories': 'calories',
    'Duration': 'duration'
})

# ------------------ Clean Gender ------------------
df['sex'] = df['sex'].str.lower().map({
    'male': 0,
    'female': 1
})

# ------------------ Force numeric conversion ------------------
numeric_cols = ['age', 'height_cm', 'weight_kg', 'duration', 'calories']

for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# ------------------ Drop invalid rows ------------------
df = df.dropna(subset=['sex', 'age', 'height_cm', 'weight_kg', 'duration', 'calories'])

# ------------------ Features & target ------------------
X_cal = df[['sex', 'age', 'height_cm', 'weight_kg', 'duration']]
y_cal = df['calories']

# ------------------ Train calories model ------------------
cal_model = RandomForestRegressor(random_state=42)
cal_model.fit(X_cal, y_cal)

joblib.dump(cal_model, "cal_model.pkl")

# ------------------ Hydration model ------------------
df['hydration_ml'] = df['weight_kg'] * 35

hydration_model = RandomForestRegressor(random_state=42)
hydration_model.fit(X_cal, df['hydration_ml'])

joblib.dump(hydration_model, "hydration_model.pkl")

print("✅ Calories & Hydration models trained successfully")
