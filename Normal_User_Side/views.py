from django.contrib import messages
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.db.models import Sum
from .ml.predict import predict_land_price
from core.models import Project, ProjectRoad, ProjectLandUse, ProjectFacility, ProjectEnvironmentalFactor
from django.contrib.auth.decorators import login_required
from .forms import UserForm, ProjectForm, ProjectRoadFormSet




User = get_user_model()

@login_required
def dashboard(request):
    completed_count = request.user.projects.filter(status='COMPLETED').count()
    draft_count = request.user.projects.filter(status='DRAFT').count()
    total_estimated_price = (
        request.user.projects
        .aggregate(total=Sum('estimated_price'))
        ['total'] or 0
    )
    recent_projects = (
        request.user.projects
        .order_by('-created_at')[:3]
    )

    context = { 'completed_count': completed_count, 'draft_count': draft_count, 'total_estimated_price': total_estimated_price, 'recent_projects': recent_projects}
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
            return redirect('normal_user:profile', pk = user.id)
    context = {"form":form}

    return render(request, 'Normal_User_Side/edit_profile.html', context)

@login_required
def newProject(request, project_id=None):
    """
    Create a new project or edit an existing one.
    """
    if project_id:
        project = get_object_or_404(Project, pk=project_id)
        is_edit = True
    else:
        project = None
        is_edit = False

    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        road_formset = ProjectRoadFormSet(request.POST, instance=project)
        print(form.errors)
        print(road_formset.errors)
        print(road_formset.non_form_errors())


        if form.is_valid() and road_formset.is_valid():
            project = form.save(commit=False)
            if not is_edit:
                project.created_by = request.user

            action = request.POST.get('action')

            if action == 'complete':
                project.status = 'COMPLETED'
            else:
                project.status = 'DRAFT'
                project.estimated_price = None  # clear price if draft

            project.save()

            # Clear existing related objects if editing
            if is_edit:
                ProjectLandUse.objects.filter(project=project).delete()
                ProjectFacility.objects.filter(project=project).delete()
                ProjectEnvironmentalFactor.objects.filter(project=project).delete()

            # Save many-to-many relationships
            for land_use in form.cleaned_data.get('land_uses', []):
                ProjectLandUse.objects.create(project=project, land_use_type=land_use)

            for facility in form.cleaned_data.get('facilities', []):
                ProjectFacility.objects.create(project=project, facility_type=facility)

            for factor in form.cleaned_data.get('environmental_factors', []):
                ProjectEnvironmentalFactor.objects.create(
                    project=project,
                    environmental_factor_type=factor
                )

            # Save roads formset
            road_formset.instance = project
            road_formset.save()

            # Predict estimated price if completed
            if action == 'complete':
                predicted_price = predict_land_price(project, road_formset)
                project.estimated_price = predicted_price
                project.save(update_fields=['estimated_price', 'status'])
                messages.success(
                    request,
                    f'Project "{project.project_name}" has been saved and marked as completed! Estimated price: {predicted_price:.0f} k JOD'
                )
            else:
                project.save(update_fields=['status'])
                messages.success(
                    request,
                    f'Project "{project.project_name}" has been saved as draft!'
                )

            return redirect('normal_user:projects')
        else:
            messages.error(request, 'Please correct the errors below.')

    else:
        # GET request
        initial = {}
        if project:
            # Pre-fill multi-select fields for editing
            initial = {
                'land_uses': project.land_uses.filter(deleted_at__isnull=True)
                               .values_list('land_use_type', flat=True),
                'facilities': project.projectfacility_set.filter(deleted_at__isnull=True)
                               .values_list('facility_type', flat=True),
                'environmental_factors': project.projectenvironmentalfactor_set.filter(deleted_at__isnull=True)
                               .values_list('environmental_factor_type', flat=True),
            }

        form = ProjectForm(instance=project, initial=initial)

        road_formset = ProjectRoadFormSet(
            instance=project,
            queryset=ProjectRoad.objects.filter(project=project, deleted_at__isnull=True) if project else ProjectRoad.objects.none()
        )

    context = {
        'form': form,
        'road_formset': road_formset,
        'is_edit': is_edit,
        'project': project,
    }

    return render(request, 'Normal_User_Side/new_project.html', context)


@login_required
def viewProjects(request):
     projects = Project.objects.filter(created_by=request.user)
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

     context = {
        'projects': projects,
        'land_types': Project.LandType.choices,
        'political_types': Project.PoliticalClassification.choices,
        'statuses': Project.Status.choices,
    }
     return render(request, 'Normal_User_Side/projects.html',context)



