from django.contrib import admin
from core.models import (
    Governorate, Town, Area, Neighborhood,
    LandUseType, FacilityType, EnvironmentalFactorType,
    Project, 
    ProjectRoad, MLModel, Setting, Valuation
)


@admin.register(Governorate)
class GovernorateAdmin(admin.ModelAdmin):
    list_display = ['code', 'name_ar', 'created_at', 'deleted_at']
    list_filter = ['deleted_at']
    search_fields = ['code', 'name_ar']
    readonly_fields = ['created_at', 'updated_at', 'code']  # code is auto-generated
    exclude = ['code']  # Hide code field from form


@admin.register(Town)
class TownAdmin(admin.ModelAdmin):
    list_display = ['code', 'name_ar', 'governorate', 'created_at', 'deleted_at']
    list_filter = ['governorate', 'deleted_at']
    search_fields = ['code', 'name_ar']
    readonly_fields = ['created_at', 'updated_at', 'code']  # code is auto-generated
    exclude = ['code']  # Hide code field from form


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ['code', 'name_ar', 'town', 'created_at', 'deleted_at']
    list_filter = ['town', 'deleted_at']
    search_fields = ['code', 'name_ar']
    readonly_fields = ['created_at', 'updated_at', 'code']  # code is auto-generated
    exclude = ['code']  # Hide code field from form


@admin.register(Neighborhood)
class NeighborhoodAdmin(admin.ModelAdmin):
    list_display = ['code', 'number', 'name_ar', 'area', 'created_at', 'deleted_at']
    list_filter = ['area', 'deleted_at']
    search_fields = ['code', 'number', 'name_ar']
    readonly_fields = ['created_at', 'updated_at', 'code']  # code is auto-generated like Area
    exclude = ['code']  # Hide code from form (auto-generated)
    # 'number' field is editable by admins for Neighborhood Number


@admin.register(LandUseType)
class LandUseTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'label', 'created_at', 'deleted_at']
    list_filter = ['deleted_at']
    search_fields = ['code', 'label']
    readonly_fields = ['created_at', 'updated_at', 'code']  # code is auto-generated
    exclude = ['code']  # Hide code field from form


@admin.register(FacilityType)
class FacilityTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'label', 'created_at', 'deleted_at']
    list_filter = ['deleted_at']
    search_fields = ['code', 'label']
    readonly_fields = ['created_at', 'updated_at', 'code']  # code is auto-generated
    exclude = ['code']  # Hide code field from form


@admin.register(EnvironmentalFactorType)
class EnvironmentalFactorTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'label', 'created_at', 'deleted_at']
    list_filter = ['deleted_at']
    search_fields = ['code', 'label']
    readonly_fields = ['created_at', 'updated_at', 'code']  # code is auto-generated
    exclude = ['code']  # Hide code field from form




class ProjectRoadInline(admin.TabularInline):
    model = ProjectRoad
    extra = 1
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['project_name', 'created_by', 'status', 'neighborhood', 'area_m2', 'created_at', 'deleted_at']
    list_filter = ['status', 'land_type', 'political_classification', 'deleted_at', 'created_at']
    search_fields = ['project_name', 'neighborhood_no', 'parcel_no']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ProjectRoadInline]
    
    fieldsets = (
        ('Project Information', {
            'fields': ('created_by', 'project_name', 'description', 'status')
        }),
        ('Location & Parcel', {
            'fields': ('neighborhood', 'neighborhood_no', 'parcel_no')
        }),
        ('Land Attributes', {
            'fields': ('area_m2', 'land_type', 'political_classification', 'slope', 'view_quality', 'parcel_shape')
        }),
        ('Utilities', {
            'fields': ('electricity', 'water', 'sewage')
        }),
        ('Ownership & Pricing', {
            'fields': ('ownership_document_type', 'actual_price_per_m2')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MLModel)
class MLModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'version', 'created_by', 'created_at', 'deleted_at']
    list_filter = ['deleted_at', 'created_at']
    search_fields = ['name', 'version']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    list_display = ['id', 'active_ml_model', 'updated_at']
    readonly_fields = ['updated_at']


@admin.register(Valuation)
class ValuationAdmin(admin.ModelAdmin):
    list_display = ['project', 'model', 'predicted_price_per_m2', 'created_by', 'created_at', 'deleted_at']
    list_filter = ['deleted_at', 'created_at']
    search_fields = ['project__project_name']
    readonly_fields = ['created_at']
