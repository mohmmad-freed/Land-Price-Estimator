from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, ActivationCode

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('email', 'name', 'type', 'is_staff', 'is_active')
    list_filter = ('type', 'is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('name',)}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('User Type', {'fields': ('type',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'password1', 'password2', 'type', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)



@admin.register(ActivationCode)
class ActivationCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'user_type', 'is_used', 'assigned_to', 'created_at')
    list_filter = ('user_type', 'is_used')
    search_fields = ('code',)
    readonly_fields = ('is_used',)