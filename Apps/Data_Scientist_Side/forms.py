from django import forms
from Apps.core.models import MLModel


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


class ModelTestForm(forms.Form):
    """Form for uploading test dataset to evaluate ML model."""
    test_file = forms.FileField(
        label="Test Dataset (CSV/Excel)",
        help_text="Upload a file containing feature columns and actual_price_per_m2 for evaluation",
        widget=forms.FileInput(attrs={
            'class': 'form-input',
            'accept': '.csv,.xlsx,.xls'
        })
    )

    def clean_test_file(self):
        file = self.cleaned_data.get('test_file')
        if file:
            # Validate extension
            valid_extensions = ['.csv', '.xlsx', '.xls']
            ext = '.' + file.name.split('.')[-1].lower()
            if ext not in valid_extensions:
                raise forms.ValidationError(
                    "Invalid file format. Please upload a CSV or Excel file."
                )
            # Max 10MB
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError("File size must be under 10MB.")
        return file
