from django.contrib import messages
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import JsonResponse
from .ml.predict import predict_land_price
from Apps.core.models import Project, ProjectRoad, Valuation, Setting, Town, Area, Neighborhood
from django.contrib.auth.decorators import login_required
from .forms import UserForm, ProjectForm, ProjectRoadFormSet
from django.db.models import F



User = get_user_model()

@login_required
def dashboard(request):
    def format_price(value):
        if value >= 1_000_000:
            return f"{value / 1_000_000:.2f}M"
        elif value >= 1_000:
            return f"{value / 1_000:.1f}k"
        else:
            return f"{value:.0f}"
    
    # Get all projects for the user
    all_projects = Project.objects.filter(created_by=request.user)
    
    # Get recent projects
    recent_projects = all_projects.order_by('-created_at')[:6]

    # Prepare values for recent projects template display
    for project in recent_projects:
        # Safely convert Decimals to floats
        try:
            project.estimated_price_float = float(project.estimated_price) if project.estimated_price is not None else 0.0
        except (TypeError, ValueError):
            project.estimated_price_float = 0.0
        
        try:
            project.area_m2_float = float(project.area_m2) if project.area_m2 is not None else 0.0
        except (TypeError, ValueError):
            project.area_m2_float = 0.0
        
        # Pre-calculate total value to avoid arithmetic in template
        project.total_estimated_value = project.estimated_price_float * project.area_m2_float
        project.total_estimated_value_formatted = format_price(project.total_estimated_value)  # ADD THIS LINE

    # Calculate total estimated value for ALL projects
    total_estimated_price = 0.0
    for project in all_projects:
        try:
            price = float(project.estimated_price) if project.estimated_price is not None else 0.0
            area = float(project.area_m2) if project.area_m2 is not None else 0.0
            total_estimated_price += price * area
        except (TypeError, ValueError):
            continue

    completed_count = all_projects.filter(status='COMPLETED').count()
    draft_count = all_projects.filter(status='DRAFT').count()

    context = {
        'recent_projects': recent_projects,
        'completed_count': completed_count,
        'draft_count': draft_count,
        'total_estimated_price': total_estimated_price,
        'total_estimated_price_formatted': format_price(total_estimated_price),
    }
    return render(request, 'Normal_User_Side/dashboard.html', context)


@login_required(login_url='users:login')
def profile(request,pk):
    user = User.objects.get(id = pk)
    return render(request, 'Normal_User_Side/profile.html')

@login_required(login_url='users:login')
def editProfile(request):
    user = request.user
    form = UserForm(instance=user)
    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            user = form.save(commit=False)  # Don't save to DB yet
            new_password = form.cleaned_data.get("new_password")
            if new_password:
                 user.set_password(new_password)
            user.save()
            return redirect('normal:profile', pk = user.id)
    context = {"form":form}

    return render(request, 'Normal_User_Side/edit_profile.html', context)

@login_required
def newProject(request, project_id=None):
    """
    Create or edit a project.
    Roads: only 'road_status' and 'width_m', start empty.
    Remove road checkbox sets defaults for ML model.
    Parcel price is calculated as estimated_price * area_m2
    """
    def format_price(value):
        if value is None:
            return "N/A"
        try:
            value = float(value)
            if value >= 1_000_000:
               return f"{value / 1_000_000:.1f}M"
            elif value >= 1_000:
               return f"{value / 1_000:.0f}k"
            else:
                return f"{value:.0f}"
        except (TypeError, ValueError):
           return "0"
    if project_id:
        project = get_object_or_404(Project, pk=project_id)
        is_edit = True
    else:
        project = None
        is_edit = False

    # Initialize parcel_price at the top level
    parcel_price = None
    if project and project.estimated_price and project.area_m2:
        parcel_price = float(project.estimated_price) * float(project.area_m2)

    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        road_formset = ProjectRoadFormSet(request.POST, instance=project)

        if form.is_valid() and road_formset.is_valid():
            # Save parent project first
            project = form.save(commit=False)
            if not is_edit:
                project.created_by = request.user

            action = request.POST.get('action')
            project.status = 'COMPLETED' if action == 'complete' else 'DRAFT'
            project.save()  # parent must exist before saving related objects

            # Save roads (only road_status & width_m)
            for road_form in road_formset:
                road_data = road_form.cleaned_data
                if road_data:
                    if road_data.get('DELETE', False):
                        # Actually delete the road instead of marking with FALSE
                        if road_form.instance.pk:
                            road_form.instance.delete()
                    else:
                        road = road_form.save(commit=False)
                        road.project = project
                        road.save()

            # Predict price if project is completed
            if action == 'complete':
                try:
                    predicted_price = predict_land_price(project, road_formset)
                    if predicted_price is None:
                        messages.error(
                            request,
                            'Unable to generate price estimate. Please ensure all required fields are filled correctly.'
                        )
                        project.status = 'DRAFT'
                        project.save(update_fields=['status'])
                        return redirect('normal:projects')
                    
                    project.estimated_price = predicted_price
                    project.save(update_fields=['estimated_price', 'status'])
                    
                    # Create Valuation record for history tracking
                    try:
                        setting = Setting.objects.first()
                        if setting and setting.active_ml_model:
                            # Soft-delete any existing valuation for this project
                            Valuation.objects.filter(
                                project=project, 
                                deleted_at__isnull=True
                            ).update(deleted_at=timezone.now())
                            
                            # Create new valuation
                            Valuation.objects.create(
                                project=project,
                                model=setting.active_ml_model,
                                predicted_price_per_m2=predicted_price,
                                created_by=request.user
                            )
                    except Exception:
                        # Don't fail the whole operation if valuation creation fails
                        pass
                    
                    parcel_price = predicted_price * float(project.area_m2 or 0)
    
                    messages.success(
                        request,
                        f'Project "{project.project_name}" saved and completed! '
                        f'Estimated price: {predicted_price:.2f} JOD/m², '
                        f'Total parcel value: {format_price(parcel_price)} JOD'
                    )
                except Exception as e:
                    messages.error(
                        request,
                        f'Error generating price estimate: {str(e)}. Project saved as draft.'
                    )
                    project.status = 'DRAFT'
                    project.save(update_fields=['status'])
            else:
                project.save(update_fields=['status'])
                messages.success(
                    request,
                    f'Project "{project.project_name}" saved as draft!'
                )

            return redirect('normal:projects')

        else:
            messages.error(request, 'Please correct the errors below.')

    else:
    # GET request: initialize form & road formset
     form = ProjectForm(instance=project)
     road_formset = ProjectRoadFormSet(
        instance=project,
        queryset=ProjectRoad.objects.filter(
            project=project, 
            deleted_at__isnull=True
        ) if project else ProjectRoad.objects.none()
    )
    
    
      
    context = {
        'form': form,
        'road_formset': road_formset,
        'is_edit': is_edit,
        'project': project,
        'parcel_price_formatted': format_price(parcel_price), 
    }

    return render(request, 'Normal_User_Side/new_project.html', context)





@login_required
def viewProjects(request):
    def format_price(value):
        if value is None:
            return "N/A"
        try:
            value = float(value)
            if value >= 1_000_000:
                return f"{value / 1_000_000:.1f}M"
            elif value >= 1_000:
                return f"{value / 1_000:.1f}k"
            else:
                return f"{value:.0f}"
        except (TypeError, ValueError):
            return "0"
    
    projects = Project.objects.filter(created_by=request.user, deleted_at__isnull=True)
    
    # Get filter parameters from GET request
    land_type = request.GET.get('land_type')
    political_type = request.GET.get('political_type')
    status = request.GET.get('status')
    search_query = request.GET.get('search')
    sort_by = request.GET.get('sort', '-created_at')

    # Apply filters in the view
    if land_type:
        projects = projects.filter(land_type=land_type)
    if political_type:
        projects = projects.filter(political_classification=political_type)
    if status:
        projects = projects.filter(status=status)
    if search_query:
        projects = projects.filter(project_name__icontains=search_query)
    
    # Apply sorting
    if sort_by in ['created_at', '-created_at']:
        projects = projects.order_by(sort_by)
    else:
        projects = projects.order_by('-created_at')

    # Calculate and format total parcel value for each project
    for project in projects:
        if project.estimated_price and project.area_m2:
            parcel_value = float(project.estimated_price) * float(project.area_m2)
            project.parcel_value = parcel_value
            project.parcel_value_formatted = format_price(parcel_value)
        else:
            project.parcel_value = None
            project.parcel_value_formatted = "N/A"

    context = {
        'projects': projects,
        'land_types': Project.LandType.choices,
        'political_types': Project.PoliticalClassification.choices,
        'statuses': Project.Status.choices,
    }
    return render(request, 'Normal_User_Side/projects.html', context)


@login_required
def deleteProject(request, project_id):
    project = get_object_or_404(Project, pk=project_id, created_by=request.user)
    
    if request.method == 'POST':
        project_name = project.project_name
        
        # Delete related records first to avoid ProtectedError
        ProjectRoad.objects.filter(project=project).delete()
        Valuation.objects.filter(project=project).delete()
        
        # Now delete the project itself
        project.delete()
        
        messages.success(request, f'Project "{project_name}" has been permanently deleted.')
        return redirect('normal:projects')
    
    return redirect('normal:projects')


# ============================================
# JSON API Endpoints for Cascading Dropdowns
# ============================================

def get_towns(request):
    """Returns towns for a given governorate_id as JSON."""
    governorate_id = request.GET.get('governorate_id')
    if not governorate_id:
        return JsonResponse([], safe=False)
    
    towns = Town.objects.filter(
        governorate_id=governorate_id,
        deleted_at__isnull=True
    ).values('id', 'name_ar').order_by('name_ar')
    return JsonResponse(list(towns), safe=False)


def get_areas(request):
    """Returns areas for a given town_id as JSON."""
    town_id = request.GET.get('town_id')
    if not town_id:
        return JsonResponse([], safe=False)
    
    areas = Area.objects.filter(
        town_id=town_id,
        deleted_at__isnull=True
    ).values('id', 'name_ar').order_by('name_ar')
    return JsonResponse(list(areas), safe=False)


def get_neighborhoods(request):
    """Returns neighborhoods for a given area_id as JSON, including code."""
    area_id = request.GET.get('area_id')
    if not area_id:
        return JsonResponse([], safe=False)
    
    neighborhoods = Neighborhood.objects.filter(
        area_id=area_id,
        deleted_at__isnull=True
    ).values('id', 'name_ar', 'code', 'number').order_by('name_ar')
    return JsonResponse(list(neighborhoods), safe=False)


def get_neighborhood_code(request):
    """Returns the number for a specific neighborhood."""
    neighborhood_id = request.GET.get('neighborhood_id')
    if not neighborhood_id:
        return JsonResponse({'code': ''})
    
    try:
        neighborhood = Neighborhood.objects.get(
            id=neighborhood_id,
            deleted_at__isnull=True
        )
        return JsonResponse({'code': neighborhood.number or ''})
    except Neighborhood.DoesNotExist:
        return JsonResponse({'code': ''})


import json

@login_required
def api_predict_price(request):
    """
    AJAX endpoint to validate form and get ML prediction.
    Returns JSON with prediction result for modal display.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    project_id = request.POST.get('project_id')
    if project_id:
        project = get_object_or_404(Project, pk=project_id)
        is_edit = True
    else:
        project = None
        is_edit = False
    
    from .forms import ProjectForm, ProjectRoadFormSet
    
    form = ProjectForm(request.POST, instance=project)
    road_formset = ProjectRoadFormSet(request.POST, instance=project)
    
    if form.is_valid() and road_formset.is_valid():
        # Save project as draft temporarily
        project = form.save(commit=False)
        if not is_edit:
            project.created_by = request.user
        project.status = 'DRAFT'  # Keep as draft until confirmed
        project.save()
        
        # Save roads
        for road_form in road_formset:
            road_data = road_form.cleaned_data
            if road_data:
                if road_data.get('DELETE', False):
                    if road_form.instance.pk:
                        road_form.instance.delete()
                else:
                    road = road_form.save(commit=False)
                    road.project = project
                    road.save()
        
        # Get prediction
        try:
            predicted_price = predict_land_price(project, road_formset)
            if predicted_price is None:
                return JsonResponse({
                    'success': False,
                    'error': 'Unable to generate price estimate. Please ensure all fields are filled correctly.'
                })
            
            parcel_price = predicted_price * float(project.area_m2 or 0)
            
            return JsonResponse({
                'success': True,
                'project_id': project.id,
                'project_name': project.project_name,
                'predicted_price_per_m2': round(predicted_price, 2),
                'area_m2': float(project.area_m2),
                'total_parcel_value': round(parcel_price, 2),
                'neighborhood': project.neighborhood.name_ar if project.neighborhood else '',
                'parcel_no': project.parcel_no,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error generating prediction: {str(e)}'
            })
    else:
        # Form validation failed
        errors = {}
        for field, error_list in form.errors.items():
            errors[field] = [str(e) for e in error_list]
        for i, road_form in enumerate(road_formset):
            for field, error_list in road_form.errors.items():
                errors[f'road_{i}_{field}'] = [str(e) for e in error_list]
        
        return JsonResponse({
            'success': False,
            'validation_errors': errors,
            'error': 'Please correct the errors below.'
        })


@login_required
def api_confirm_prediction(request):
    """
    AJAX endpoint to confirm or reject prediction.
    Accepts: project_id, action (accept/reject), user_expected_price (optional)
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = request.POST
    
    project_id = data.get('project_id')
    action = data.get('action')  # 'accept' or 'reject'
    user_expected_price = data.get('user_expected_price')
    
    if not project_id or not action:
        return JsonResponse({'success': False, 'error': 'Missing required fields'})
    
    project = get_object_or_404(Project, pk=project_id, created_by=request.user)
    
    if action == 'accept':
        # Finalize the project as completed
        try:
            predicted_price = predict_land_price(project, None)
            project.estimated_price = predicted_price
            project.status = 'COMPLETED'
            project.save(update_fields=['estimated_price', 'status'])
            
            # Create Valuation record
            setting = Setting.objects.first()
            if setting and setting.active_ml_model:
                Valuation.objects.filter(
                    project=project, 
                    deleted_at__isnull=True
                ).update(deleted_at=timezone.now())
                
                valuation = Valuation.objects.create(
                    project=project,
                    model=setting.active_ml_model,
                    predicted_price_per_m2=predicted_price,
                    created_by=request.user
                )
                
                # Store user's expected price if provided
                if user_expected_price:
                    try:
                        valuation.user_expected_price = float(user_expected_price)
                        valuation.save(update_fields=['user_expected_price'])
                    except (ValueError, TypeError):
                        pass
            
            return JsonResponse({
                'success': True,
                'action': 'accepted',
                'redirect_url': '/normal/projects/'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    elif action == 'reject':
        # Keep project as draft
        project.status = 'DRAFT'
        project.save(update_fields=['status'])
        
        # Still store the user's expected price for ML training
        if user_expected_price:
            setting = Setting.objects.first()
            if setting and setting.active_ml_model:
                try:
                    predicted_price = predict_land_price(project, None)
                    Valuation.objects.filter(
                        project=project, 
                        deleted_at__isnull=True
                    ).update(deleted_at=timezone.now())
                    
                    Valuation.objects.create(
                        project=project,
                        model=setting.active_ml_model,
                        predicted_price_per_m2=predicted_price,
                        user_expected_price=float(user_expected_price),
                        created_by=request.user
                    )
                except Exception:
                    pass
        
        return JsonResponse({
            'success': True,
            'action': 'rejected',
            'redirect_url': '/normal/projects/'
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid action'})
