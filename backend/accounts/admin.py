from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Identity', {'fields': ('phone', 'national_id')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Identity', {'fields': ('phone', 'national_id', 'email')}),
    )
    list_display = ('id', 'username', 'email', 'phone', 'national_id', 'is_staff')
    search_fields = ('username', 'email', 'phone', 'national_id')
