import joblib
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL_PATH = os.path.join(BASE_DIR, "ml", "land_price_model.pkl")
FEATURES_PATH = os.path.join(BASE_DIR, "ml", "model_features.pkl")

model = joblib.load(MODEL_PATH)
model_features = joblib.load(FEATURES_PATH)
