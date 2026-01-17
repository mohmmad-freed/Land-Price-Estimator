from django import forms
from core.models import MLModel


class MLModelUploadForm(forms.ModelForm):
    """Form for uploading ML model files."""
    model_file = forms.FileField(
        label="Model File (.pkl)",
        help_text="Upload a scikit-learn model saved with joblib (.pkl format)",
        widget=forms.FileInput(attrs={'class': 'form-input', 'accept': '.pkl'})
    )

    class Meta:
        model = MLModel
        fields = ['name', 'version', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., Land Price Model v2'
            }),
            'version': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., 2.0.1'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 4,
                'placeholder': 'Describe the model, training data, and improvements...'
            }),
        }

    def clean_model_file(self):
        file = self.cleaned_data.get('model_file')
        if file:
            if not file.name.endswith('.pkl'):
                raise forms.ValidationError("Only .pkl files are allowed.")
            # Max 50MB
            if file.size > 50 * 1024 * 1024:
                raise forms.ValidationError("File size must be under 50MB.")
        return file
