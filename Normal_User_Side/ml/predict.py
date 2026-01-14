import pandas as pd
from .model_loader import get_model

def predict_land_price(project, road_formset=None):
    model = get_model()

    paved_roads = ["FALSE", "FALSE", "FALSE"]

    # Use formset if provided
    if road_formset:
        for i, road_form in enumerate(road_formset.forms[:3]):
            if road_form.cleaned_data and not road_form.cleaned_data.get('DELETE', False):
                status = road_form.cleaned_data.get('road_status', 'FALSE')
                paved_roads[i] = status
    else:
        roads = project.projectroad_set.all()[:3]
        for i, road in enumerate(roads):
            paved_roads[i] = road.road_status

    input_dict = {
        "Area": project.area,
        "Neighborhood": project.neighborhood,
        "land_type": project.land_type,
        "political_classification": project.political_classification,
        "parcel_shape": project.parcel_shape,
        "facility_types": (
            project.projectfacility_set.first().facility_type.label
            if project.projectfacility_set.exists()
            else "NONE"
        ),
        "Paved Road1": paved_roads[0],
        "Paved Road2": paved_roads[1],
        "Paved Road3": paved_roads[2],
        "area_m2": float(project.area_m2),
        "width_m": float(
            road_formset.forms[0].cleaned_data['width_m']
            if road_formset and road_formset.forms
            else (project.projectroad_set.first().width_m if project.projectroad_set.exists() else 0)
        ),
    }

    df = pd.DataFrame([input_dict])
    prediction = model.predict(df)
    return float(prediction[0])



