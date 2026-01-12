import joblib
import os
from django.conf import settings

MODEL_PATH = os.path.join(
    settings.BASE_DIR,
    "Normal_User_Side",
    "ml",
    "land_price_model.pkl"
)

_model = None

def get_model():
    global _model
    if _model is None:
        _model = joblib.load(MODEL_PATH)
    return _model

