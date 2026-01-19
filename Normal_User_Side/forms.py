from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import re
from django.contrib.auth.hashers import check_password
from django.forms import inlineformset_factory
from core.models import (
    Project, Governorate, Town, Area, Neighborhood, ProjectRoad
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


class ProjectRoadForm(forms.ModelForm):
    """Custom form for ProjectRoad that auto-derives road_ownership from road_status."""
    
    class Meta:
        model = ProjectRoad
        fields = ['road_status', 'width_m']
        widgets = {
            'road_status': forms.Select(attrs={'class': 'form-select'}),
            'width_m': forms.NumberInput(attrs={'class': 'form-input', 'min': '0.01', 'step': '0.01'}),
        }
        labels = {
            'road_status': 'Road Status',
            'width_m': 'Road Width (m)',
        }
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Auto-derive road_ownership from road_status
        road_status = self.cleaned_data.get('road_status', '')
        if road_status.startswith('PUBLIC'):
            instance.road_ownership = 'PUBLIC'
        elif road_status.startswith('PRIVATE'):
            instance.road_ownership = 'PRIVATE'
        else:
            # Default to PUBLIC for 'FALSE' (No Road) or unknown
            instance.road_ownership = 'PUBLIC'
        
        # Auto-derive is_paved from road_status
        instance.is_paved = 'PAVED' in road_status and 'UNPAVED' not in road_status
        
        if commit:
            instance.save()
        return instance


ProjectRoadFormSet = inlineformset_factory(
    Project,
    ProjectRoad,
    form=ProjectRoadForm,
    can_delete=True,
    max_num=3,
    extra=3,
)


class ProjectForm(forms.ModelForm):
    # Helper fields for location hierarchy
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
            'parcel_frontage',
            'electricity',
            'water',
            'sewage',
            'ownership_document_type',
            # Land Use boolean fields
            'land_use_residential',
            'land_use_commercial',
            'land_use_agricultural',
            'land_use_industrial',
            # Facility boolean fields
            'hospitals_facility',
            'schools_facility',
            'police_facility',
            'municipality_facility',
            # Environmental factor boolean fields
            'FACTORIES_NEARBY',
            'NOISY_FACILITIES',
            'ANIMAL_FARMS',
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
            'parcel_frontage': forms.NumberInput(attrs={'class': 'form-input', 'min': '0', 'step': '0.01', 'placeholder': 'e.g., 25.00'}),
            'electricity': forms.Select(attrs={'class': 'form-select'}),
            'water': forms.Select(attrs={'class': 'form-select'}),
            'sewage': forms.Select(attrs={'class': 'form-select'}),
            'ownership_document_type': forms.Select(attrs={'class': 'form-select'}),
            # Checkbox widgets for boolean fields
            'land_use_residential': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'land_use_commercial': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'land_use_agricultural': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'land_use_industrial': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'hospitals_facility': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'schools_facility': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'police_facility': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'municipality_facility': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'FACTORIES_NEARBY': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'NOISY_FACILITIES': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'ANIMAL_FARMS': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
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
            'parcel_frontage': 'Parcel Frontage (m)',
            'electricity': 'Electricity',
            'water': 'Water Supply',
            'sewage': 'Sewage System',
            'ownership_document_type': 'Ownership Document Type',
            # Land Use labels
            'land_use_residential': 'Residential',
            'land_use_commercial': 'Commercial',
            'land_use_agricultural': 'Agricultural',
            'land_use_industrial': 'Industrial',
            # Facility labels
            'hospitals_facility': 'Hospitals Nearby',
            'schools_facility': 'Schools Nearby',
            'police_facility': 'Police Station Nearby',
            'municipality_facility': 'Municipality Nearby',
            # Environmental factor labels
            'FACTORIES_NEARBY': 'Factories Nearby',
            'NOISY_FACILITIES': 'Noisy Facilities',
            'ANIMAL_FARMS': 'Animal Farms Nearby',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter out soft-deleted neighborhoods
        self.fields['neighborhood'].queryset = Neighborhood.objects.filter(deleted_at__isnull=True)
        # Make neighborhood_no not required
        self.fields['neighborhood_no'].required = False
        
    def clean_area_m2(self):
        area = self.cleaned_data.get('area_m2')
        if area and area <= 0:
            raise ValidationError("Land area must be greater than 0.")
        return area
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validate at least one land use is selected
        land_use_residential = cleaned_data.get('land_use_residential')
        land_use_commercial = cleaned_data.get('land_use_commercial')
        land_use_agricultural = cleaned_data.get('land_use_agricultural')
        land_use_industrial = cleaned_data.get('land_use_industrial')
        
        if not any([land_use_residential, land_use_commercial, land_use_agricultural, land_use_industrial]):
            raise ValidationError('Please select at least one intended land use.')
        
        # Check for duplicate parcel (neighborhood + neighborhood_no + parcel_no)
        neighborhood = cleaned_data.get('neighborhood')
        neighborhood_no = cleaned_data.get('neighborhood_no')
        parcel_no = cleaned_data.get('parcel_no')
        
        if neighborhood and neighborhood_no and parcel_no:
            existing = Project.objects.filter(
                neighborhood=neighborhood,
                neighborhood_no=neighborhood_no,
                parcel_no=parcel_no,
                deleted_at__isnull=True  # Respect soft-deleted records
            )
            # Exclude current instance if editing
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError(
                    f'A project with parcel number "{parcel_no}" in neighborhood "{neighborhood_no}" already exists. '
                    'Please use different values or edit the existing project.'
                )
        
        return cleaned_data

