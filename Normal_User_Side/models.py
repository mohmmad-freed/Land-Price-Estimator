from django.db import models

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

    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    land_type = models.CharField(max_length=50, choices=LAND_TYPES)
    political_classification = models.CharField(max_length=50, choices=POLITICAL)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    date_created = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.name
