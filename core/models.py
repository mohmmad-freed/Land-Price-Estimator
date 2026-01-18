from django.db import models
from django.db.models import Q
from django.conf import settings
from core.mixins import AutoCodeMixin


class Governorate(AutoCodeMixin, models.Model):
    code = models.CharField(max_length=50, blank=True)
    name_ar = models.CharField(max_length=150)
    
    # AutoCodeMixin configuration
    _code_source_fields = ['name_ar']
    _code_parent_field = None  # Global uniqueness
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name_ar
    
    class Meta:
        db_table = 'governorates'
        constraints = [
            models.UniqueConstraint(
                fields=['code'],
                condition=Q(deleted_at__isnull=True),
                name='uq_governorate_code_active'
            )
        ]


class Town(AutoCodeMixin, models.Model):
    governorate = models.ForeignKey(Governorate, on_delete=models.PROTECT)
    code = models.CharField(max_length=50, blank=True)
    name_ar = models.CharField(max_length=150)
    
    # AutoCodeMixin configuration
    _code_source_fields = ['name_ar']
    _code_parent_field = 'governorate'  # Unique within governorate
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name_ar
    
    class Meta:
        db_table = 'towns'
        constraints = [
            models.UniqueConstraint(
                fields=['governorate', 'code'],
                condition=Q(deleted_at__isnull=True),
                name='uq_town_governorate_code_active'
            )
        ]


class Area(AutoCodeMixin, models.Model):
    town = models.ForeignKey(Town, on_delete=models.PROTECT)
    code = models.CharField(max_length=50, blank=True)
    name_ar = models.CharField(max_length=150)
    
    # AutoCodeMixin configuration
    _code_source_fields = ['name_ar']
    _code_parent_field = 'town'  # Unique within town
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name_ar
    
    class Meta:
        db_table = 'areas'
        constraints = [
            models.UniqueConstraint(
                fields=['town', 'code'],
                condition=Q(deleted_at__isnull=True),
                name='uq_area_town_code_active'
            )
        ]


class Neighborhood(AutoCodeMixin, models.Model):
    area = models.ForeignKey(Area, on_delete=models.PROTECT)
    code = models.CharField(max_length=50, blank=True)
    name_ar = models.CharField(max_length=150)
    
    # AutoCodeMixin configuration
    _code_source_fields = ['name_ar']
    _code_parent_field = 'area'  # Unique within area
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name_ar
    
    class Meta:
        db_table = 'neighborhoods'
        constraints = [
            models.UniqueConstraint(
                fields=['area', 'code'],
                condition=Q(deleted_at__isnull=True),
                name='uq_neighborhood_area_code_active'
            )
        ]


class LandUseType(AutoCodeMixin, models.Model):
    code = models.CharField(max_length=30, blank=True)
    label = models.CharField(max_length=100)
    
    # AutoCodeMixin configuration
    _code_source_fields = ['label']
    _code_parent_field = None  # Global uniqueness
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.label
    
    class Meta:
        db_table = 'land_use_types'
        constraints = [
            models.UniqueConstraint(
                fields=['code'],
                condition=Q(deleted_at__isnull=True),
                name='uq_land_use_type_code_active'
            )
        ]


class FacilityType(AutoCodeMixin, models.Model):
    code = models.CharField(max_length=30, blank=True)
    label = models.CharField(max_length=100)
    
    # AutoCodeMixin configuration
    _code_source_fields = ['label']
    _code_parent_field = None  # Global uniqueness
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.label
    
    class Meta:
        db_table = 'facility_types'
        constraints = [
            models.UniqueConstraint(
                fields=['code'],
                condition=Q(deleted_at__isnull=True),
                name='uq_facility_type_code_active'
            )
        ]


class EnvironmentalFactorType(AutoCodeMixin, models.Model):
    code = models.CharField(max_length=50, blank=True)
    label = models.CharField(max_length=120)
    
    # AutoCodeMixin configuration
    _code_source_fields = ['label']
    _code_parent_field = None  # Global uniqueness
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.label
    
    class Meta:
        db_table = 'environmental_factor_types'
        constraints = [
            models.UniqueConstraint(
                fields=['code'],
                condition=Q(deleted_at__isnull=True),
                name='uq_environmental_factor_type_code_active'
            )
        ]


class Project(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        COMPLETED = 'COMPLETED', 'Completed'

    class LandType(models.TextChoices):
        PRIVATE = 'PRIVATE', 'Private'
        COMMON_SHARE = 'COMMON_SHARE', 'Common Share'
        PUBLIC = 'PUBLIC', 'Public'

    class PoliticalClassification(models.TextChoices):
        AREA_A = 'AREA_A', ' A'
        AREA_B = 'AREA_B', ' B'
        AREA_C = 'AREA_C', ' C'

    class Slope(models.TextChoices):
        FLAT = 'FLAT', 'Flat'
        MILD = 'MILD', 'Mild'
        MODERATE = 'MODERATE', 'Moderate'
        STEEP = 'STEEP', 'Steep'

    class ViewQuality(models.TextChoices):
        BAD = 'BAD', 'Bad'
        GOOD = 'GOOD', 'Good'
        FANTASTIC = 'FANTASTIC', 'Fantastic'

    class ParcelShape(models.TextChoices):
        SQUARE = 'SQUARE', 'Square'
        RECTANGLE = 'RECTANGLE', 'Rectangle'
        TRIANGLE = 'TRIANGLE', 'Triangle'
        IRREGULAR = 'IRREGULAR', 'Irregular'

    class Electricity(models.TextChoices):
        YES_3PHASE = 'YES_3PHASE', 'Yes 3-Phase'
        YES_1PHASE = 'YES_1PHASE', 'Yes 1-Phase'
        NO = 'NO', 'No'

    class Water(models.TextChoices):
        YES = 'YES', 'Yes'
        NO = 'NO', 'No'

    class Sewage(models.TextChoices):
        YES_PRIVATE = 'YES_PRIVATE', 'Yes Private'
        YES_PUBLIC = 'YES_PUBLIC', 'Yes Public'
        NO = 'NO', 'No'

    class OwnershipDocumentType(models.TextChoices):
        TABU = 'TABU', 'Tabu'
        FINAL_SETTLEMENT = 'FINAL_SETTLEMENT', 'Final Settlement'
        ONGOING_SETTLEMENT = 'ONGOING_SETTLEMENT', 'Ongoing Settlement'
        DURABLE_POA = 'DURABLE_POA', 'Durable POA'
        SALE_CONTRACT = 'SALE_CONTRACT', 'Sale Contract'
        HUJJA = 'HUJJA', 'Hujja'
        GIFT = 'GIFT', 'Gift'

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='projects')
    project_name = models.CharField(max_length=150)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    governorate = models.ForeignKey(Governorate, on_delete=models.PROTECT)
    town = models.ForeignKey(Town, on_delete=models.PROTECT)
    area = models.ForeignKey(Area, on_delete=models.PROTECT)  
    neighborhood = models.ForeignKey(Neighborhood, on_delete=models.PROTECT)
    neighborhood_no = models.CharField(max_length=50)
    parcel_no = models.CharField(max_length=50)
    land_type = models.CharField(max_length=20, choices=LandType.choices)
    political_classification = models.CharField(max_length=20, choices=PoliticalClassification.choices)
    slope = models.CharField(max_length=20, choices=Slope.choices)
    view_quality = models.CharField(max_length=20, choices=ViewQuality.choices)
    area_m2 = models.DecimalField(max_digits=12, decimal_places=2)
    parcel_shape = models.CharField(max_length=20, choices=ParcelShape.choices)
    electricity = models.CharField(max_length=20, choices=Electricity.choices)
    water = models.CharField(max_length=10, choices=Water.choices)
    sewage = models.CharField(max_length=20, choices=Sewage.choices)
    ownership_document_type = models.CharField(max_length=30, choices=OwnershipDocumentType.choices)
    actual_price_per_m2 = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    estimated_price = models.FloatField(null=True, blank=True, help_text="Generated by ML model")
    parcel_frontage = models.FloatField(null=True, blank=True)  # new
    land_use_residential = models.BooleanField(default=False)
    land_use_commercial = models.BooleanField(default=False)
    land_use_agricultural = models.BooleanField(default=False)
    land_use_industrial = models.BooleanField(default=False)
    hospitals_facility = models.BooleanField(default=False)
    schools_facility = models.BooleanField(default=False)
    police_facility = models.BooleanField(default=False)
    municipality_facility = models.BooleanField(default=False)
    FACTORIES_NEARBY = models.BooleanField(default=False)
    NOISY_FACILITIES = models.BooleanField(default=False)
    ANIMAL_FARMS = models.BooleanField(default=False)
    parcel_frontage = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    

    @property
    def has_electricity(self):
        return self.electricity != self.Electricity.NO

    @property
    def has_water(self):
        return self.water == self.Water.YES

    @property
    def has_sewage(self):
        return self.sewage != self.Sewage.NO

    class Meta:
        db_table = 'projects'
        constraints = [
            models.UniqueConstraint(
                fields=['neighborhood', 'neighborhood_no', 'parcel_no'],
                condition=Q(deleted_at__isnull=True),
                name='uq_project_neighborhood_parcel_active'
            )
        ]


class ProjectRoad(models.Model):
    class RoadStatus(models.TextChoices):
        PUBLIC_EXISTING_UNPAVED = 'PUBLIC_EXISTING_UNPAVED', 'Public Existing Unpaved'
        PUBLIC_EXISTING_PAVED = 'PUBLIC_EXISTING_PAVED', 'Public Existing Paved'
        PRIVATE_EXISTING_UNPAVED = 'PRIVATE_EXISTING_UNPAVED', 'Private Existing Unpaved'
        PRIVATE_EXISTING_PAVED = 'PRIVATE_EXISTING_PAVED', 'Private Existing Paved'
        PRIVATE_PROPOSED_UNPAVED = 'PRIVATE_PROPOSED_UNPAVED', 'Private Proposed Unpaved'
        PUBLIC_PROPOSED_UNPAVED = 'PUBLIC_PROPOSED_UNPAVED', 'Public Proposed Unpaved'
        FALSE = 'FALSE', 'No Road'
    

    class RoadOwnership(models.TextChoices):
        PUBLIC = 'PUBLIC', 'Public'
        PRIVATE = 'PRIVATE', 'Private'

    project = models.ForeignKey(Project, on_delete=models.PROTECT)
    road_status = models.CharField(max_length=50, choices=RoadStatus.choices)
    road_ownership = models.CharField(max_length=20, choices=RoadOwnership.choices)
    is_paved = models.BooleanField(default=False)
    width_m = models.DecimalField(max_digits=6, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'project_roads'


class MLModel(models.Model):
    name = models.CharField(max_length=120)
    version = models.CharField(max_length=50)
    description = models.TextField()
    model_file_path = models.CharField(max_length=1024)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'ml_models'


class Setting(models.Model):
    active_ml_model = models.ForeignKey(MLModel, on_delete=models.PROTECT, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'settings'


class Valuation(models.Model):
    project = models.ForeignKey(Project, on_delete=models.PROTECT)
    model = models.ForeignKey(MLModel, on_delete=models.PROTECT)
    predicted_price_per_m2 = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'valuations'
        constraints = [
            models.UniqueConstraint(
                fields=['project'],
                condition=Q(deleted_at__isnull=True),
                name='uq_valuation_project_active'
            )
        ]
