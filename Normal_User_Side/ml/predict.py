import pandas as pd
from .model_loader import get_model

def predict_land_price(project, road_formset=None):
    model = get_model()  # your joblib-loaded model

    # ----------------------------
    # Roads (default = no road)
    # ----------------------------
    road_statuses = ["FALSE", "FALSE", "FALSE"]
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
    # Land uses (multi-select)
    # ----------------------------
    land_use_codes = set(project.land_uses.values_list("land_use_type__code", flat=True))

    # ----------------------------
    # Facilities / Environmental factors
    # ----------------------------
    facility_codes = set(project.projectfacility_set.values_list("facility_type__code", flat=True))
    env_codes = set(project.projectenvironmentalfactor_set.values_list("environmental_factor_type__code", flat=True))

    # ----------------------------
    # Build input row (MUST MATCH TRAINING)
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
        "width_m": road_widths[0],
        "width_m.1": road_widths[1],
        "width_m.2": road_widths[2],

        # binary: land uses
        "land_use_residential": int("RESIDENTIAL" in land_use_codes),
        "land_use_commercial": int("COMMERCIAL" in land_use_codes),
        "land_use_agricultural": int("AGRICULTURAL" in land_use_codes),
        "land_use_industrial": int("INDUSTRIAL" in land_use_codes),

        # binary: facilities
        "hospitals_facility": int("HOSPITAL" in facility_codes),
        "schools_facility": int("SCHOOL" in facility_codes),
        "police_facility": int("POLICE" in facility_codes),
        "municipality_facility": int("MUNICIPALITY" in facility_codes),

        # binary: environmental
        "FACTORIES_NEARBY": int("FACTORIES_NEARBY" in env_codes),
        "NOISY_FACILITIES": int("NOISY_FACILITIES" in env_codes),
        "ANIMAL_FARMS": int("ANIMAL_FARMS" in env_codes),

        # water as binary
        "water": int(project.water == "YES"),
    }

    df = pd.DataFrame([row])
    prediction = model.predict(df)
    return float(prediction[0])


