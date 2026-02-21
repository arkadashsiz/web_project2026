from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Role, RolePermission, UserRole

User = get_user_model()


class RolePermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RolePermission
        fields = ('id', 'action')


class RoleSerializer(serializers.ModelSerializer):
    permissions = RolePermissionSerializer(many=True, required=False)

    class Meta:
        model = Role
        fields = ('id', 'name', 'description', 'is_system', 'permissions')

    def create(self, validated_data):
        permissions = validated_data.pop('permissions', [])
        role = Role.objects.create(**validated_data)
        for p in permissions:
            RolePermission.objects.create(role=role, **p)
        return role

    def update(self, instance, validated_data):
        permissions = validated_data.pop('permissions', None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        if permissions is not None:
            instance.permissions.all().delete()
            for p in permissions:
                RolePermission.objects.create(role=instance, **p)
        return instance


class UserRoleSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    role_name = serializers.CharField(source='role.name', read_only=True)

    class Meta:
        model = UserRole
        fields = ('id', 'user', 'username', 'role', 'role_name')
