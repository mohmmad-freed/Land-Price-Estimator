from django.db import models

from Land_Price_Estimator import settings

class Project(models.Model):
    LAND_TYPES = [
        ("agricultural", "Agricultural"),
        ("residential", "Residential"),
        ("commercial", "Commercial"),
        ("industrial", "Industrial"),
        ("mixed", "Mixed Use"),
    ]

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("completed", "Completed"),
    ]

    POLITICAL = [
        ("a", "Area A"),
        ("b", "Area B"),
        ("c", "Area C"),
    ]
    GOVERNORATES = [
        ("ramallah", "Ramallah"),
        ("nablus", "Nablus"),
        ("bethlehem", "Bethlehem"),
        ("jenin", "Jenin"),
        ("hebron", "Hebron"),
        
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='projects'
    )

    name = models.CharField(max_length=255)
    governorate = models.CharField(max_length=50, choices=GOVERNORATES)
    land_size = models.PositiveIntegerField()
    land_type = models.CharField(max_length=50, choices=LAND_TYPES)
    political_classification = models.CharField(max_length=50, choices=POLITICAL)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    description = models.TextField(blank=True)
    date_created = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.name
