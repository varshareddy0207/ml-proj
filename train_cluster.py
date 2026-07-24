import pandas as pd
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.cluster import KMeans
import joblib

# ------------------ Load athlete dataset ------------------
df = pd.read_excel(r"C:\Users\somva\Desktop\athlete_events1.xlsx")

# Rename columns
df = df.rename(columns={
    'Age': 'age',
    'Height': 'height_cm',
    'Weight': 'weight_kg',
    'Sex': 'sex',
    'Sport': 'sport'
})

# Keep required columns
df = df[['sex', 'age', 'height_cm', 'weight_kg', 'sport']].dropna()

# Encode sport
sport_encoder = LabelEncoder()
df['sport_encoded'] = sport_encoder.fit_transform(df['sport'])

# Encode sex
sex_encoder = LabelEncoder()
df['sex'] = sex_encoder.fit_transform(df['sex'])

# Features
features = ['sex', 'age', 'height_cm', 'weight_kg', 'sport_encoded']
X = df[features]

# Scale
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# KMeans
kmeans = KMeans(n_clusters=4, random_state=42)
kmeans.fit(X_scaled)

# Save models
joblib.dump(kmeans, "kmeans.pkl")
joblib.dump(scaler, "scaler.pkl")
joblib.dump(sport_encoder, "sport_encoder.pkl")
joblib.dump(sex_encoder, "sex_encoder.pkl")

print("✅ Athlete clustering model trained & saved")
