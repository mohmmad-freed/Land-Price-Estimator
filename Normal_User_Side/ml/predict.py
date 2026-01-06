import pandas as pd
from Normal_User_Side.ml.model_loader import load_model

def predict_land_price(input_data):
    model, model_features = load_model()
    X = pd.DataFrame([input_data])[model_features]
    return model.predict(X)[0]