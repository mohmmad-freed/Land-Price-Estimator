import joblib
import os
from django.conf import settings

# Fallback path for original hardcoded model
FALLBACK_MODEL_PATH = os.path.join(
    settings.BASE_DIR,
    "Apps",
    "Normal_User_Side",
    "ml",
    "land_price_model.pkl"
)

_model = None
_model_path = None


def get_model():
    """
    Load the active ML model from database settings.
    Falls back to the hardcoded model if no active model is set.
    """
    global _model, _model_path
    
    # Try to get active model from database
    try:
        from core.models import Setting
        setting = Setting.objects.first()
        if setting and setting.active_ml_model:
            # Build full path from media root
            db_model_path = os.path.join(
                settings.MEDIA_ROOT,
                setting.active_ml_model.model_file_path
            )
            
            # Check if we need to reload (different model selected)
            if _model is None or _model_path != db_model_path:
                if os.path.exists(db_model_path):
                    _model = joblib.load(db_model_path)
                    _model_path = db_model_path
                    return _model
    except Exception:
        # Database not ready or other error, fall through to fallback
        pass
    
    # Fallback to original hardcoded model
    if _model is None:
        if os.path.exists(FALLBACK_MODEL_PATH):
            _model = joblib.load(FALLBACK_MODEL_PATH)
            _model_path = FALLBACK_MODEL_PATH
        else:
            raise FileNotFoundError(
                f"No ML model available. "
                f"No active model is set in the database, and the fallback model "
                f"was not found at: {FALLBACK_MODEL_PATH}"
            )

    return _model
