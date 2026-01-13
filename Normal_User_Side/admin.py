from django.contrib import admin
from .models import Project, IntendedUse


@admin.register(IntendedUse)
class IntendedUseAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_display_name']
    ordering = ['name']
    
    def get_display_name(self, obj):
        return obj.get_name_display()
    get_display_name.short_description = 'Display Name'


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'user',
        'governorate',
        'town',
        "area_m2",
        'land_type',
        'slope',
        'status',
        'date_created',
        'estimated_price'
    ]
    
    list_filter = [
        'status',
        'governorate',
        'town',
        'land_type',
        'political_classification',
        'slope',
        'has_electricity',
        'has_water',
        'has_sewage',
        'has_paved_road',
        'has_internet',
        'date_created'
    ]
    
    search_fields = ['name', 'description', 'user__email', 'user__name']
    
    filter_horizontal = ['intended_uses']
    
    readonly_fields = ['date_created']
    
    fieldsets = (
        ('Project Information', {
            'fields': ('name', 'description', 'user', 'status', 'date_created')
        }),
        ('Location Details', {
            'fields': ('governorate', 'town', 'political_classification')
        }),
        ('Land Characteristics', {
            'fields': ('land_size', 'land_type', 'slope', 'intended_uses')
        }),
        ('Infrastructure', {
            'fields': ('has_electricity', 'has_water', 'has_sewage', 'has_paved_road', 'has_internet'),
            'classes': ('collapse',)
        }),
        ('Pricing', {
            'fields': ('estimated_price',)
        }),
    )
    
    date_hierarchy = 'date_created'

