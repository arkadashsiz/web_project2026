from django.contrib.auth import get_user_model
from rest_framework import serializers
from rbac.models import Role, UserRole

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'password', 'email', 'phone', 'national_id',
            'first_name', 'last_name'
        )

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        base_role, _ = Role.objects.get_or_create(
            name='base user',
            defaults={'description': 'Default minimum access role', 'is_system': True},
        )
        UserRole.objects.get_or_create(user=user, role=base_role)
        return user


class UserSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'phone', 'national_id',
            'first_name', 'last_name', 'roles', 'is_superuser'
        )

    def get_roles(self, obj):
        return list(obj.user_roles.values_list('role__name', flat=True))
