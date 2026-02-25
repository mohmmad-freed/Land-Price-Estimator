import pandas as pd
from .model_loader import get_model

def predict_land_price(project, road_formset=None):
    model = get_model()  # your joblib-loaded model

    # ----------------------------
    # Roads (default = FALSE for ML model when no road exists)
    # ----------------------------
    road_statuses = ["FALSE", "FALSE", "FALSE"]  # ML expects 'FALSE' for no road
    road_widths = [0, 0, 0]

    roads = road_formset.forms if road_formset else project.projectroad_set.all()

    for i, road in enumerate(roads[:3]):
        # If coming from a formset
        if hasattr(road, "cleaned_data"):
            if road.cleaned_data and not road.cleaned_data.get("DELETE", False):
                road_statuses[i] = road.cleaned_data.get("road_status", "FALSE")
                road_widths[i] = road.cleaned_data.get("width_m") or 0
        # If coming from saved DB objects
        else:
            road_statuses[i] = road.road_status or "FALSE"
            road_widths[i] = float(road.width_m or 0)

    # ----------------------------
    # Build input row (MUST MATCH TRAINING)
    # Uses boolean fields directly from Project model
    # ----------------------------
    row = {
        # categorical
        "Area": project.area.name_ar,
        "Neighborhood": project.neighborhood.name_ar,
        "political_classification": project.political_classification,
        "parcel_shape": project.parcel_shape,
        "road_status1": road_statuses[0],
        "road_status2": road_statuses[1],
        "road_status3": road_statuses[2],
        "slope": project.slope,
        "view_quality": project.view_quality,
        "electricity": project.electricity,
        "Sewage": project.sewage,

        # numeric
        "area_m2": float(project.area_m2),
        "parcel_frontage (m)": float(project.parcel_frontage) if project.parcel_frontage else 0.0,
        "width_m": road_widths[0],
        "width_m.1": road_widths[1],
        "width_m.2": road_widths[2],

        # binary: land uses (using boolean fields from Project model)
        "land_use_residential": int(project.land_use_residential),
        "land_use_commercial": int(project.land_use_commercial),
        "land_use_agricultural": int(project.land_use_agricultural),
        "land_use_industrial": int(project.land_use_industrial),

        # binary: facilities (using boolean fields from Project model)
        "hospitals_facility": int(project.hospitals_facility),
        "schools_facility": int(project.schools_facility),
        "police_facility": int(project.police_facility),
        "municipality_facility": int(project.municipality_facility),

        # binary: environmental (using boolean fields from Project model)
        "FACTORIES_NEARBY": int(project.FACTORIES_NEARBY),
        "NOISY_FACILITIES": int(project.NOISY_FACILITIES),
        "ANIMAL_FARMS": int(project.ANIMAL_FARMS),

        # water as binary
        "water": int(project.water == "YES"),
    }

    df = pd.DataFrame([row])
    prediction = model.predict(df)
    return float(prediction[0])


