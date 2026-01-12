import pandas as pd
from .model_loader import get_model

def predict_land_price(project, road_formset=None):
    """
    Predict land price based on Project model instance and optional roads formset.
    """
    model = get_model()
    
    # Prepare input dictionary matching the training features
    input_dict = {
        "Area": project.area,
        "Neighborhood": project.neighborhood,
        "land_type": project.land_type,
        "political_classification": project.political_classification,
        "parcel_shape": project.parcel_shape,
        "facility_types": ",".join([f.facility_type for f in project.projectfacility_set.all()]) 
                           if project.projectfacility_set.exists() else "None",
        "Paved Road1": 0,
        "Paved Road2": 0,
        "Paved Road3": 0,
        "area_m2": project.area_m2,
        "width_m": project.width_m
    }

    # Fill paved roads from the formset if available
    if road_formset:
        for i, road_form in enumerate(road_formset):
            if i >= 3:
                break  # we only have 3 columns in the model
            key = f"Paved Road{i+1}"
            value = 1 if road_form.cleaned_data.get("is_paved") else 0
            input_dict[key] = value

    # Convert to DataFrame
    df = pd.DataFrame([input_dict])
    
    # Predict
    prediction = model.predict(df)
    
    return float(prediction[0])