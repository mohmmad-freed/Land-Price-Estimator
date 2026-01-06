from Normal_User_Side.ml.model_loader import load_model

def predict_land_price(input_data):
    model, model_features = load_model()
    return model.predict([input_data])
