import pandas as pd
from .model_loader import model, model_features

def predict_land_price(project):
    data = {
        "land_size": project.land_size,
        "land_type": project.land_type,
        "governorate": project.governorate,
        "political_classification": project.political_classification,
    }

    df = pd.DataFrame([data])
    df = pd.get_dummies(df)

    # Ensure same features as training
    df = df.reindex(columns=model_features, fill_value=0)

    predicted_price = model.predict(df)[0]
    return round(predicted_price, 2)
