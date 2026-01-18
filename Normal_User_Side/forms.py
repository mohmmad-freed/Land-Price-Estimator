from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import re
from django.contrib.auth.hashers import check_password
from django.forms import inlineformset_factory
from core.models import (
    Project, Governorate, Town, Area, Neighborhood,
    LandUseType, FacilityType, EnvironmentalFactorType, ProjectRoad
)


User = get_user_model()

class UserForm(forms.ModelForm):
    current_password = forms.CharField(widget=forms.PasswordInput, required=False)
    new_password = forms.CharField(widget=forms.PasswordInput, required=False)
    confirm_password = forms.CharField(widget=forms.PasswordInput, required=False)

    class Meta:
        model = User
        fields = ['name', 'email', 'phone']

    def clean(self):
        cleaned_data = super().clean()
        current_password = cleaned_data.get("current_password")
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password or confirm_password:
            if not current_password:
                raise ValidationError("Current password is required.")

            if not check_password(current_password, self.instance.password):
                raise ValidationError("Current password is incorrect.")

            if new_password != confirm_password:
                raise ValidationError("Passwords do not match.")

            validate_password(new_password, user=self.instance)

        return cleaned_data

    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        if phone and not re.match(r'^\+?[0-9]{7,15}$', phone):
            raise ValidationError("Enter a valid phone number.")
        return phone


ProjectRoadFormSet = inlineformset_factory(
    Project,
    ProjectRoad,
    fields=['road_status', 'width_m'],  # only the real model fields
    can_delete=True,  # allows the "Remove" checkbox automatically
    max_num=3,
    widgets={
        'road_status': forms.Select(attrs={'class': 'form-select'}),
        'width_m': forms.NumberInput(attrs={'class': 'form-input', 'min': '0.01', 'step': '0.01'}),
    },
    labels={
        'road_status': 'Road Status',
        'width_m': 'Road Width (m)',
    }
)



class ProjectForm(forms.ModelForm):
    # Helper fields for location hierarchy (not saved to Project model)
    governorate = forms.ModelChoiceField(
        queryset=Governorate.objects.filter(deleted_at__isnull=True),
        required=True,
        label="Governorate",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_governorate'}),
        help_text="Select governorate first"
    )
    
    town = forms.ModelChoiceField(
        queryset=Town.objects.filter(deleted_at__isnull=True),
        required=True,
        label="Town",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_town'}),
        help_text="Select town after governorate"
    )
    
    area = forms.ModelChoiceField(
        queryset=Area.objects.filter(deleted_at__isnull=True),
        required=True,
        label="Area",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_area'}),
        help_text="Select area after town"
    )
    
    # Many-to-many fields with checkboxes
    land_uses = forms.ModelMultipleChoiceField(
        queryset=LandUseType.objects.filter(deleted_at__isnull=True),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Intended Land Uses",
        help_text="Select at least one intended use for this land"
    )
    
    facilities = forms.ModelMultipleChoiceField(
        queryset=FacilityType.objects.filter(deleted_at__isnull=True),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Nearby Facilities",
        help_text="Select all nearby facilities"
    )
    
    environmental_factors = forms.ModelMultipleChoiceField(
        queryset=EnvironmentalFactorType.objects.filter(deleted_at__isnull=True),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Environmental Factors",
        help_text="Select all applicable environmental factors"
    )

    class Meta:
        model = Project
        fields = [
            'project_name',
            'description',
            'governorate',
            'town',
            'area',
            'neighborhood',
            'neighborhood_no',
            'parcel_no',
            'land_type',
            'political_classification',
            'slope',
            'view_quality',
            'area_m2',
            'parcel_shape',
            'electricity',
            'water',
            'sewage',
            'ownership_document_type',
        ]
        widgets = {
            'project_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter project name'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Optional project description'}),
            'neighborhood': forms.Select(attrs={'class': 'form-select'}),
            'neighborhood_no': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., 123'}),
            'parcel_no': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., 456'}),
            'land_type': forms.Select(attrs={'class': 'form-select'}),
            'political_classification': forms.Select(attrs={'class': 'form-select'}),
            'slope': forms.Select(attrs={'class': 'form-select'}),
            'view_quality': forms.Select(attrs={'class': 'form-select'}),
            'area_m2': forms.NumberInput(attrs={'class': 'form-input', 'min': '0.01', 'step': '0.01', 'placeholder': 'e.g., 500.00'}),
            'parcel_shape': forms.Select(attrs={'class': 'form-select'}),
            'electricity': forms.Select(attrs={'class': 'form-select'}),
            'water': forms.Select(attrs={'class': 'form-select'}),
            'sewage': forms.Select(attrs={'class': 'form-select'}),
            'ownership_document_type': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'project_name': 'Project Name',
            'neighborhood': 'Neighborhood',
            'neighborhood_no': 'Neighborhood Number',
            'parcel_no': 'Parcel Number',
            'land_type': 'Land Type',
            'political_classification': 'Political Classification',
            'slope': 'Land Slope',
            'view_quality': 'View Quality',
            'area_m2': 'Land Area (m²)',
            'parcel_shape': 'Parcel Shape',
            'electricity': 'Electricity',
            'water': 'Water Supply',
            'sewage': 'Sewage System',
            'ownership_document_type': 'Ownership Document Type',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter out soft-deleted neighborhoods
        self.fields['neighborhood'].queryset = Neighborhood.objects.filter(deleted_at__isnull=True)
        
    def clean_area_m2(self):
        area = self.cleaned_data.get('area_m2')
        if area and area <= 0:
            raise ValidationError("Land area must be greater than 0.")
        return area
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validate at least one land use is selected
        land_uses = cleaned_data.get('land_uses')
        if not land_uses or land_uses.count() == 0:
            self.add_error('land_uses', 'Please select at least one intended land use.')
        
        return cleaned_data


