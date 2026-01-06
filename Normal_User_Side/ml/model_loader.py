import joblib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "land_price_model.joblib"

model = None
model_features = None

def load_model():
    global model, model_features
    if model is None:
        model = joblib.load(MODEL_PATH)
        model_features = model.feature_names_in_
    return model, model_features

