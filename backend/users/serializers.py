from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Role

User = get_user_model()

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'access_level', 'description']

class UserSerializer(serializers.ModelSerializer):
    # Flatten role data for easy reading
    role_name = serializers.ReadOnlyField(source='role.name')
    access_level = serializers.ReadOnlyField(source='role.access_level')

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone_number', 
            'national_id', 'role', 'role_name', 'access_level', "first_name", "last_name",
        ]

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'phone_number', 'national_id', "first_name", "last_name"]

    def create(self, validated_data):
        # Securely hash the password
        civilian_role = Role.objects.filter(name='Civilian').first()
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email'),
            password=validated_data['password'],
            phone_number=validated_data.get('phone_number'),
            national_id=validated_data.get('national_id'),
            first_name=validated_data.get('first_name'),
            last_name=validated_data.get('last_name'),
            role=civilian_role
        )
        return user
