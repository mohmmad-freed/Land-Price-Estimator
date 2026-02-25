import os
import io
import pandas as pd
import joblib
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponse
from django.conf import settings
from django.utils import timezone
from django.db import models
from django.db.models import Count, Avg, Q
from django.core.paginator import Paginator
from Apps.Normal_User_Side.forms import UserForm
from Apps.core.models import MLModel, Setting, Valuation, Project
from .forms import MLModelUploadForm, ModelTestForm
from datetime import timedelta
from django.utils import timezone
from collections import defaultdict
import json
from sklearn.metrics import mean_absolute_error, r2_score


def scientist_required(view_func):
    """Decorator that checks if user is a Data Scientist."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('users:login')
        if request.user.type not in ('scientist', 'data_scientist'):
            return HttpResponseForbidden("Access denied. Data Scientists only.")
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required(login_url='users:login')
@scientist_required
def dashboard(request):
    """Data Scientist dashboard view."""
    # Get model statistics
    total_models = MLModel.objects.filter(deleted_at__isnull=True).count()
    active_model = None
    try:
        setting = Setting.objects.first()
        if setting:
            active_model = setting.active_ml_model
    except Setting.DoesNotExist:
        pass
    
    # Get valuation statistics
    total_valuations = Valuation.objects.filter(deleted_at__isnull=True).count()
    recent_valuations = Valuation.objects.filter(
        deleted_at__isnull=True
    ).select_related('project', 'model', 'created_by').order_by('-created_at')[:5]
    
    # Get models with their valuation counts
    models_with_stats = MLModel.objects.filter(
        deleted_at__isnull=True
    ).annotate(
        valuation_count=Count('valuation', filter=models.Q(valuation__deleted_at__isnull=True))
    ).order_by('-valuation_count')[:5]
    
    context = {
        'user': request.user,
        'total_models': total_models,
        'active_model': active_model,
        'total_valuations': total_valuations,
        'recent_valuations': recent_valuations,
        'models_with_stats': models_with_stats,
    }
    return render(request, 'Data_Scientist_Side/dashboard.html', context)


@login_required(login_url='users:login')
@scientist_required
def profile(request):
    """Data Scientist profile view."""
    return render(request, 'Data_Scientist_Side/profile.html')


@login_required(login_url='users:login')
@scientist_required
def editProfile(request):
    """Data Scientist edit profile view."""
    user = request.user
    form = UserForm(instance=user)
    
    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            user = form.save(commit=False)
            new_password = form.cleaned_data.get("new_password")
            if new_password:
                user.set_password(new_password)
            user.save()
            return redirect('data_scientist:profile')
    
    context = {"form": form}
    return render(request, 'Data_Scientist_Side/edit_profile.html', context)


# ============================================
# ML Model Management Views
# ============================================

@login_required(login_url='users:login')
@scientist_required
def model_list(request):
    """List all ML models with active status."""
    models = MLModel.objects.filter(deleted_at__isnull=True).order_by('-created_at')
    
    # Get active model
    active_model_id = None
    try:
        setting = Setting.objects.first()
        if setting and setting.active_ml_model:
            active_model_id = setting.active_ml_model.id
    except Setting.DoesNotExist:
        pass
    
    context = {
        'models': models,
        'active_model_id': active_model_id,
    }
    return render(request, 'Data_Scientist_Side/model_list.html', context)


@login_required(login_url='users:login')
@scientist_required
def model_upload(request):
    """Upload a new ML model."""
    if request.method == 'POST':
        form = MLModelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            model = form.save(commit=False)
            model.created_by = request.user
            
            # Save uploaded file
            uploaded_file = request.FILES['model_file']
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{model.name.replace(' ', '_')}_{model.version}_{timestamp}.pkl"
            
            # Ensure directory exists
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'ml_models')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save file
            file_path = os.path.join(upload_dir, filename)
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            
            # Store relative path in database
            model.model_file_path = os.path.join('ml_models', filename)
            model.save()
            
            messages.success(request, f'Model "{model.name}" v{model.version} uploaded successfully!')
            return redirect('data_scientist:model_list')
    else:
        form = MLModelUploadForm()
    
    context = {'form': form}
    return render(request, 'Data_Scientist_Side/model_upload.html', context)


@login_required(login_url='users:login')
@scientist_required
def model_activate(request, model_id):
    """Set a model as the active model for predictions."""
    model = get_object_or_404(MLModel, pk=model_id, deleted_at__isnull=True)
    
    # Get or create settings
    setting, created = Setting.objects.get_or_create(pk=1)
    setting.active_ml_model = model
    setting.save()
    
    messages.success(request, f'Model "{model.name}" v{model.version} is now active!')
    return redirect('data_scientist:model_list')


@login_required(login_url='users:login')
@scientist_required
def model_detail(request, model_id):
    """View details of a specific model."""
    model = get_object_or_404(MLModel, pk=model_id, deleted_at__isnull=True)
    
    # Check if this is the active model
    is_active = False
    try:
        setting = Setting.objects.first()
        if setting and setting.active_ml_model and setting.active_ml_model.id == model.id:
            is_active = True
    except Setting.DoesNotExist:
        pass
    
    # Get usage statistics
    valuation_count = Valuation.objects.filter(model=model, deleted_at__isnull=True).count()
    
    # Get recent valuations for this model
    recent_valuations = Valuation.objects.filter(
        model=model, deleted_at__isnull=True
    ).select_related('project', 'created_by').order_by('-created_at')[:10]
    
    context = {
        'model': model,
        'is_active': is_active,
        'valuation_count': valuation_count,
        'recent_valuations': recent_valuations,
    }
    return render(request, 'Data_Scientist_Side/model_detail.html', context)


@login_required(login_url='users:login')
@scientist_required
def valuation_list(request):
    """List all valuations with filtering by model."""
    # Get filter parameters
    model_filter = request.GET.get('model', '')
    
    # Base queryset
    valuations = Valuation.objects.filter(
        deleted_at__isnull=True
    ).select_related('project', 'model', 'created_by').order_by('-created_at')
    
    # Apply model filter
    if model_filter:
        valuations = valuations.filter(model_id=model_filter)
    
    # Pagination
    paginator = Paginator(valuations, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all models for filter dropdown
    models = MLModel.objects.filter(deleted_at__isnull=True).order_by('name')
    
    context = {
        'page_obj': page_obj,
        'models': models,
        'model_filter': model_filter,
        'total_count': valuations.count(),
    }
    return render(request, 'Data_Scientist_Side/valuation_list.html', context)


# ============================================
# Statistics & Analytics Views
# ============================================

@login_required(login_url='users:login')
@scientist_required
def statistics(request):
    """Comprehensive statistics dashboard for Data Scientists."""
    
    # ─── Get Active Model ───
    active_model = None
    try:
        setting = Setting.objects.first()
        if setting:
            active_model = setting.active_ml_model
    except Setting.DoesNotExist:
        pass
    
    # ─── Overview Statistics (filtered by active model) ───
    total_models = MLModel.objects.filter(deleted_at__isnull=True).count()
    total_projects = Project.objects.filter(deleted_at__isnull=True).count()
    
    # Base queryset filtered by active model
    if active_model:
        base_valuations = Valuation.objects.filter(deleted_at__isnull=True, model=active_model)
    else:
        base_valuations = Valuation.objects.filter(deleted_at__isnull=True)
    
    total_valuations = base_valuations.count()
    
    # Valuations with feedback (user_expected_price provided)
    valuations_with_feedback = base_valuations.filter(
        user_expected_price__isnull=False
    ).count()
    feedback_rate = round((valuations_with_feedback / total_valuations * 100), 1) if total_valuations > 0 else 0
    
    # ─── Model Accuracy Metrics (filtered by active model) ───
    # Get valuations where we have both predicted and expected prices
    feedback_valuations = base_valuations.filter(
        user_expected_price__isnull=False
    ).values('predicted_price_per_m2', 'user_expected_price')
    
    # Calculate Mean Absolute Error and Average Deviation
    total_error = 0
    total_deviation_percent = 0
    feedback_count = len(feedback_valuations)
    
    for v in feedback_valuations:
        predicted = float(v['predicted_price_per_m2'])
        expected = float(v['user_expected_price'])
        error = abs(predicted - expected)
        total_error += error
        if expected > 0:
            total_deviation_percent += (error / expected) * 100
    
    mae = round(total_error / feedback_count, 2) if feedback_count > 0 else 0
    avg_deviation = round(total_deviation_percent / feedback_count, 1) if feedback_count > 0 else 0
    accuracy_score = max(0, round(100 - avg_deviation, 1)) if feedback_count > 0 else None
    
    # ─── Valuations Over Time (Last 30 Days, filtered by active model) ───
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    
    daily_valuations = base_valuations.filter(
        created_at__date__gte=thirty_days_ago
    ).values('created_at__date').annotate(count=Count('id')).order_by('created_at__date')
    
    # Build complete date range with zeros for missing days
    date_counts = {str(item['created_at__date']): item['count'] for item in daily_valuations}
    chart_dates = []
    chart_counts = []
    for i in range(31):  # Include today (30 days ago through today = 31 days)
        date = thirty_days_ago + timedelta(days=i)
        chart_dates.append(date.strftime('%b %d'))
        chart_counts.append(date_counts.get(str(date), 0))
    
    # ─── Geographic Distribution ───
    geo_distribution = Project.objects.filter(
        deleted_at__isnull=True,
        valuation__deleted_at__isnull=True
    ).values('governorate__name_ar').annotate(
        count=Count('valuation')
    ).order_by('-count')[:8]
    
    geo_labels = [item['governorate__name_ar'] or 'Unknown' for item in geo_distribution]
    geo_data = [item['count'] for item in geo_distribution]
    
    # ─── Model Performance Comparison ───
    model_stats = MLModel.objects.filter(deleted_at__isnull=True).annotate(
        valuation_count=Count('valuation', filter=Q(valuation__deleted_at__isnull=True)),
        feedback_count=Count('valuation', filter=Q(
            valuation__deleted_at__isnull=True,
            valuation__user_expected_price__isnull=False
        )),
        avg_predicted=Avg('valuation__predicted_price_per_m2', filter=Q(valuation__deleted_at__isnull=True))
    ).order_by('-valuation_count')
    
    model_names = []
    model_valuation_counts = []
    model_feedback_counts = []
    
    for m in model_stats:
        model_names.append(f"{m.name} v{m.version}")
        model_valuation_counts.append(m.valuation_count)
        model_feedback_counts.append(m.feedback_count)
    
    # ─── Predicted vs Expected Comparison Data (filtered by active model) ───
    comparison_data = base_valuations.filter(
        user_expected_price__isnull=False
    ).select_related('project').order_by('-created_at')[:20]
    
    comparison_labels = []
    predicted_values = []
    expected_values = []
    
    for v in comparison_data:
        comparison_labels.append(v.project.project_name[:15] if v.project else f"Val #{v.id}")
        predicted_values.append(float(v.predicted_price_per_m2))
        expected_values.append(float(v.user_expected_price))
    
    # Reverse to show chronologically
    comparison_labels.reverse()
    predicted_values.reverse()
    expected_values.reverse()
    
    # ─── Recent Feedback Table (filtered by active model) ───
    recent_feedback = base_valuations.filter(
        user_expected_price__isnull=False
    ).select_related('project', 'model', 'created_by').order_by('-created_at')[:10]
    
    context = {
        # Active Model Info
        'active_model': active_model,
        
        # Overview Stats
        'total_valuations': total_valuations,
        'total_models': total_models,
        'total_projects': total_projects,
        'valuations_with_feedback': valuations_with_feedback,
        'feedback_rate': feedback_rate,
        
        # Accuracy Metrics
        'mae': mae,
        'avg_deviation': avg_deviation,
        'accuracy_score': accuracy_score,
        'feedback_count': feedback_count,
        
        # Chart Data (JSON for JavaScript)
        'chart_dates_json': json.dumps(chart_dates),
        'chart_counts_json': json.dumps(chart_counts),
        'geo_labels_json': json.dumps(geo_labels),
        'geo_data_json': json.dumps(geo_data),
        'model_names_json': json.dumps(model_names),
        'model_valuation_counts_json': json.dumps(model_valuation_counts),
        'model_feedback_counts_json': json.dumps(model_feedback_counts),
        'comparison_labels_json': json.dumps(comparison_labels),
        'predicted_values_json': json.dumps(predicted_values),
        'expected_values_json': json.dumps(expected_values),
        
        # Recent feedback for table
        'recent_feedback': recent_feedback,
    }
    return render(request, 'Data_Scientist_Side/statistics.html', context)


# ============================================
# Model Testing Views
# ============================================

# Mapping from user-friendly slope values to ML model format
SLOPE_MAPPING = {
    'Flat (0-5%)': 'FLAT',
    'FLAT': 'FLAT',
    'Mild (5-15%)': 'MILD',
    'MILD': 'MILD',
    'Moderate (15-30%)': 'MODERATE',
    'MODERATE': 'MODERATE',
    'Steep (>30%)': 'STEEP',
    'STEEP': 'STEEP',
}

# View quality mapping (handle typos like FANTACTIC)
VIEW_QUALITY_MAPPING = {
    'BAD': 'BAD',
    'GOOD': 'GOOD',
    'FANTASTIC': 'FANTASTIC',
    'FANTACTIC': 'FANTASTIC',  # Common typo
}

# Required columns for ML model (must match predict.py)
REQUIRED_ML_COLUMNS = [
    'Area', 'Neighborhood', 'political_classification', 'parcel_shape',
    'road_status1', 'road_status2', 'road_status3', 'slope', 'view_quality',
    'electricity', 'Sewage', 'area_m2', 'parcel_frontage (m)',
    'width_m', 'width_m.1', 'width_m.2',
    'land_use_residential', 'land_use_commercial', 'land_use_agricultural',
    'land_use_industrial', 'hospitals_facility', 'schools_facility',
    'police_facility', 'municipality_facility', 'FACTORIES_NEARBY',
    'NOISY_FACILITIES', 'ANIMAL_FARMS', 'water',
]
TARGET_COLUMN = 'actual_price_per_m2'

# Columns in user's file format
USER_FILE_COLUMNS = [
    'Area', 'Neighborhood', 'political_classification', 'slope', 'view_quality',
    'area_m2', 'parcel_frontage (m)', 'parcel_shape', 'electricity', 'water', 'Sewage',
    'road_status1', 'road_status2', 'road_status3',
    'land_use_residential', 'land_use_commercial', 'land_use_agricultural', 'land_use_industrial',
    'hospitals_facility', 'schools_facility', 'police_facility', 'municipality_facility',
    'FACTORIES_NEARBY', 'NOISY_FACILITIES', 'ANIMAL_FARMS',
    'actual_price_per_m2'
]


def preprocess_test_data(df):
    """
    Transform user's CSV/Excel data to match ML model's expected format.
    Handles column renaming, value mappings, and data type conversions.
    """
    result = pd.DataFrame()
    
    # Copy location columns directly
    result['Area'] = df['Area']
    result['Neighborhood'] = df['Neighborhood']
    result['political_classification'] = df['political_classification']
    result['parcel_shape'] = df['parcel_shape']
    
    # Handle road statuses - convert FALSE to proper ML format
    for i, col_name in enumerate(['road_status1', 'road_status2', 'road_status3']):
        if col_name in df.columns:
            result[col_name] = df[col_name].fillna('FALSE').replace('', 'FALSE')
        else:
            result[col_name] = 'FALSE'
    
    # Map slope values to ML format
    if 'slope' in df.columns:
        result['slope'] = df['slope'].map(lambda x: SLOPE_MAPPING.get(str(x).strip(), 'FLAT'))
    else:
        result['slope'] = 'FLAT'
    
    # Map view_quality values (handle typos)
    if 'view_quality' in df.columns:
        result['view_quality'] = df['view_quality'].map(
            lambda x: VIEW_QUALITY_MAPPING.get(str(x).strip().upper(), 'GOOD')
        )
    else:
        result['view_quality'] = 'GOOD'
    
    # Copy electricity and Sewage
    result['electricity'] = df['electricity'] if 'electricity' in df.columns else 'NO'
    result['Sewage'] = df['Sewage'] if 'Sewage' in df.columns else 'NO'
    
    # Numeric columns
    result['area_m2'] = pd.to_numeric(df['area_m2'], errors='coerce').fillna(0)
    
    if 'parcel_frontage (m)' in df.columns:
        result['parcel_frontage (m)'] = pd.to_numeric(df['parcel_frontage (m)'], errors='coerce').fillna(0)
    else:
        result['parcel_frontage (m)'] = 0
    
    # Handle width_m columns - user file may have multiple columns with same name
    # or may have them as width_m, width_m, width_m (which pandas renames to width_m, width_m.1, width_m.2)
    width_cols = [c for c in df.columns if c.startswith('width_m')]
    for i, ml_col in enumerate(['width_m', 'width_m.1', 'width_m.2']):
        if i < len(width_cols):
            result[ml_col] = pd.to_numeric(df[width_cols[i]], errors='coerce').fillna(0)
        else:
            result[ml_col] = 0
    
    # Binary columns - convert TRUE/FALSE strings to 1/0
    binary_columns = [
        'land_use_residential', 'land_use_commercial', 'land_use_agricultural',
        'land_use_industrial', 'hospitals_facility', 'schools_facility',
        'police_facility', 'municipality_facility', 'FACTORIES_NEARBY',
        'NOISY_FACILITIES', 'ANIMAL_FARMS'
    ]
    
    for col in binary_columns:
        if col in df.columns:
            result[col] = df[col].map(lambda x: 1 if str(x).upper() in ['TRUE', '1', 'YES'] else 0)
        else:
            result[col] = 0
    
    # Water - convert YES/NO to 1/0 for ML
    if 'water' in df.columns:
        result['water'] = df['water'].map(lambda x: 1 if str(x).upper() == 'YES' else 0)
    else:
        result['water'] = 0
    
    return result


@login_required(login_url='users:login')
@scientist_required
def model_test(request, model_id):
    """Test an ML model with an external dataset."""
    model_obj = get_object_or_404(MLModel, pk=model_id, deleted_at__isnull=True)
    
    if request.method == 'POST':
        form = ModelTestForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['test_file']
            
            try:
                # Read the file based on extension
                file_ext = uploaded_file.name.split('.')[-1].lower()
                
                if file_ext == 'csv':
                    # Try to detect delimiter (comma or semicolon)
                    content = uploaded_file.read().decode('utf-8')
                    uploaded_file.seek(0)  # Reset file pointer
                    
                    # Count occurrences of potential delimiters in first line
                    first_line = content.split('\n')[0]
                    semicolon_count = first_line.count(';')
                    comma_count = first_line.count(',')
                    
                    delimiter = ';' if semicolon_count > comma_count else ','
                    df = pd.read_csv(io.StringIO(content), delimiter=delimiter)
                else:
                    df = pd.read_excel(uploaded_file)
                
                # Check for empty dataframe
                if df.empty:
                    messages.error(request, "The uploaded file is empty.")
                    return render(request, 'Data_Scientist_Side/model_test.html', {
                        'form': form,
                        'model': model_obj,
                        'user_columns': USER_FILE_COLUMNS,
                    })
                
                # Check for target column
                if TARGET_COLUMN not in df.columns:
                    messages.error(
                        request,
                        f"Missing target column: '{TARGET_COLUMN}'. This column is required for evaluation."
                    )
                    return render(request, 'Data_Scientist_Side/model_test.html', {
                        'form': form,
                        'model': model_obj,
                        'user_columns': USER_FILE_COLUMNS,
                    })
                
                # Check for minimum required columns
                required_base = ['Area', 'Neighborhood', 'area_m2']
                missing = [c for c in required_base if c not in df.columns]
                if missing:
                    messages.error(
                        request,
                        f"Missing required columns: {', '.join(missing)}"
                    )
                    return render(request, 'Data_Scientist_Side/model_test.html', {
                        'form': form,
                        'model': model_obj,
                        'user_columns': USER_FILE_COLUMNS,
                    })
                
                # Extract actual prices before preprocessing
                y_actual = pd.to_numeric(df[TARGET_COLUMN], errors='coerce').fillna(0).values
                
                # Preprocess data to match ML model format
                try:
                    X = preprocess_test_data(df)
                except Exception as prep_error:
                    messages.error(
                        request,
                        f"Data preprocessing error: {str(prep_error)}"
                    )
                    return render(request, 'Data_Scientist_Side/model_test.html', {
                        'form': form,
                        'model': model_obj,
                        'user_columns': USER_FILE_COLUMNS,
                    })
                
                # Load the specific model
                model_path = os.path.join(settings.MEDIA_ROOT, model_obj.model_file_path)
                if not os.path.exists(model_path):
                    messages.error(request, "Model file not found on server.")
                    return redirect('data_scientist:model_detail', model_id=model_id)
                
                ml_model = joblib.load(model_path)
                
                # Ensure columns are in correct order for model
                X = X[REQUIRED_ML_COLUMNS]
                
                # Run batch predictions
                try:
                    y_predicted = ml_model.predict(X)
                except Exception as pred_error:
                    messages.error(
                        request,
                        f"Prediction error: {str(pred_error)}. Please check your data format."
                    )
                    return render(request, 'Data_Scientist_Side/model_test.html', {
                        'form': form,
                        'model': model_obj,
                        'user_columns': USER_FILE_COLUMNS,
                    })
                
                # Calculate metrics
                mae = mean_absolute_error(y_actual, y_predicted)
                r2 = r2_score(y_actual, y_predicted)
                
                # Build results DataFrame
                results_df = df.copy()
                results_df['predicted_price_per_m2'] = y_predicted
                results_df['deviation'] = y_predicted - y_actual
                results_df['deviation_percent'] = ((y_predicted - y_actual) / y_actual * 100).round(2)
                
                # Store results in session for download
                request.session['test_results'] = results_df.to_json()
                request.session['test_model_id'] = model_id
                request.session['test_model_name'] = f"{model_obj.name} v{model_obj.version}"
                
                # Prepare display data (limit to first 100 rows for display)
                display_results = []
                for idx, row in results_df.head(100).iterrows():
                    display_results.append({
                        'row_num': idx + 1,
                        'area': row.get('Area', 'N/A'),
                        'neighborhood': row.get('Neighborhood', 'N/A'),
                        'area_m2': row.get('area_m2', 0),
                        'actual': round(float(row[TARGET_COLUMN]), 2),
                        'predicted': round(float(row['predicted_price_per_m2']), 2),
                        'deviation': round(float(row['deviation']), 2),
                        'deviation_percent': round(float(row['deviation_percent']), 1),
                    })
                
                context = {
                    'model': model_obj,
                    'mae': round(mae, 2),
                    'r2': round(r2, 4),
                    'r2_percent': round(r2 * 100, 1),
                    'sample_count': len(df),
                    'display_count': min(100, len(df)),
                    'results': display_results,
                    'has_more': len(df) > 100,
                }
                return render(request, 'Data_Scientist_Side/model_test_results.html', context)
                
            except pd.errors.EmptyDataError:
                messages.error(request, "The uploaded file is empty or corrupted.")
            except pd.errors.ParserError:
                messages.error(request, "Could not parse the file. Please check the format.")
            except Exception as e:
                messages.error(request, f"Error processing file: {str(e)}")
    else:
        form = ModelTestForm()
    
    context = {
        'form': form,
        'model': model_obj,
        'user_columns': USER_FILE_COLUMNS,
    }
    return render(request, 'Data_Scientist_Side/model_test.html', context)


@login_required(login_url='users:login')
@scientist_required
def download_test_results(request):
    """Download the test results as CSV."""
    results_json = request.session.get('test_results')
    model_name = request.session.get('test_model_name', 'model')
    
    if not results_json:
        messages.error(request, "No test results available. Please run a test first.")
        return redirect('data_scientist:model_list')
    
    try:
        df = pd.read_json(results_json)
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        filename = f"test_results_{model_name.replace(' ', '_')}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        df.to_csv(response, index=False)
        return response
        
    except Exception as e:
        messages.error(request, f"Error generating download: {str(e)}")
        return redirect('data_scientist:model_list')
