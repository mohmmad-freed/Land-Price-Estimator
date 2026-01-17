import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.conf import settings
from django.utils import timezone
from Normal_User_Side.forms import UserForm
from core.models import MLModel, Setting, Valuation
from .forms import MLModelUploadForm


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
    
    context = {
        'user': request.user,
        'total_models': total_models,
        'active_model': active_model,
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
    
    context = {
        'model': model,
        'is_active': is_active,
        'valuation_count': valuation_count,
    }
    return render(request, 'Data_Scientist_Side/model_detail.html', context)

