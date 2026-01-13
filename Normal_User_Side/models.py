from django.db import models

from Land_Price_Estimator import settings
from .constants import (
    LAND_TYPES,
    POLITICAL_CLASSIFICATIONS,
    GOVERNORATES,
    STATUS_CHOICES,
    TOWN_CHOICES,
    AREA_CHOICES,
    NEIGHBORHOOD_CHOICES,
    SLOPE_CHOICES,
    INTENDED_USE_CHOICES,
    PARCEL_SHAPE_CHOICES,
    ROAD_STATUS_CHOICES
)


class IntendedUse(models.Model):
    """
    Represents a specific intended use type for land.
    This is a lookup table with predefined values.
    """
    name = models.CharField(
        max_length=50,
        choices=INTENDED_USE_CHOICES,
        unique=True
    )

    class Meta:
        ordering = ['name']
        verbose_name = "Intended Use"
        verbose_name_plural = "Intended Uses"

    def __str__(self):
        return self.get_name_display()


class Project(models.Model):
    # Keep legacy class attributes for backward compatibility
    LAND_TYPES = LAND_TYPES
    STATUS_CHOICES = STATUS_CHOICES
    POLITICAL = POLITICAL_CLASSIFICATIONS
    GOVERNORATES = GOVERNORATES

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='projects'
    )

    # Basic project info
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    date_created = models.DateField(auto_now_add=True)
    estimated_price = models.FloatField(null=True, blank=True)

    # Original land fields
    governorate = models.CharField(max_length=50, choices=GOVERNORATES)
    area_m2 = models.PositiveIntegerField(null=True, blank=True)
    land_type = models.CharField(max_length=50, choices=LAND_TYPES)
    political_classification = models.CharField(max_length=50, choices=POLITICAL_CLASSIFICATIONS)
    width_m = models.FloatField(null=True, blank=True)

    # NEW FIELDS - All nullable/blank to avoid breaking existing projects
    # Validation enforced in form layer
    town = models.CharField(
        max_length=50,
        choices=TOWN_CHOICES,
        blank=True,
        null=True,
        help_text="Town within the governorate"
    )

    area = models.CharField(
        max_length=100,
        choices=AREA_CHOICES,
        blank=True,
        null=True,
        help_text="Area within the town"
    )

    neighborhood = models.CharField(
        max_length=100,
        choices=NEIGHBORHOOD_CHOICES,
        blank=True,
        null=True,
        help_text="Neighborhood/District within the area"
    )

    slope = models.CharField(
        max_length=20,
        choices=SLOPE_CHOICES,
        blank=True,
        null=True,
        help_text="Degree of land slope"
    )

    parcel_shape = models.CharField(
    max_length=20,
    choices=PARCEL_SHAPE_CHOICES,
    null=True,
    blank=True

    )
    
    facility_type_ml = models.CharField(
    max_length=30,
    null=True,
    blank=True

    )

    paved_road_1 = models.CharField(max_length=20, choices=ROAD_STATUS_CHOICES, null=True, blank=True)
    paved_road_2 = models.CharField(max_length=20, choices=ROAD_STATUS_CHOICES, null=True, blank=True)
    paved_road_3 = models.CharField(max_length=20, choices=ROAD_STATUS_CHOICES, null=True, blank=True)


    # Infrastructure availability (boolean fields)
    has_electricity = models.BooleanField(default=False, help_text="Electricity available")
    has_water = models.BooleanField(default=False, help_text="Water supply available")
    has_sewage = models.BooleanField(default=False, help_text="Sewage system available")
    has_paved_road = models.BooleanField(default=False, help_text="Paved road access")
    has_internet = models.BooleanField(default=False, help_text="Internet connectivity available")

    # Intended land uses (ManyToMany relationship)
    intended_uses = models.ManyToManyField(
        IntendedUse,
        blank=True,
        related_name='projects',
        help_text="Intended use(s) for this land"
    )

    def __str__(self):
        return self.name

