from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import re
from django.contrib.auth.hashers import check_password

from Normal_User_Side.models import Project


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
    

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            'name',
            'governorate',
            'land_type',
            'political_classification',
            'status',
            'description',
            'land_size'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg'}),
            'governorate': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg'}),
            'land_size': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg', 'min': 1}),
            'land_type': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg'}),
            'political_classification': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border rounded-lg', 'rows': 5}),
        }
