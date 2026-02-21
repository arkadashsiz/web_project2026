from django.contrib import admin
from .models import Role, RolePermission, UserRole

admin.site.register(Role)
admin.site.register(RolePermission)
admin.site.register(UserRole)
