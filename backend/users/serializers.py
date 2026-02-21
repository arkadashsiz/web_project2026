from rest_framework import serializers, exceptions
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Role, RoleRequest

User = get_user_model()


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'access_level', 'description']


class UserSerializer(serializers.ModelSerializer):
    roles_list = serializers.SerializerMethodField()
    highest_access_level = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone_number',
            'national_id', 'roles_list', 'highest_access_level',
            'first_name', 'last_name',
        ]

    def get_roles_list(self, obj) -> list:
        return list(obj.roles.values_list('name', flat=True))


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'phone_number', 'national_id', "first_name", "last_name"]

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email'),
            password=validated_data['password'],
            phone_number=validated_data.get('phone_number'),
            national_id=validated_data.get('national_id'),
            first_name=validated_data.get('first_name'),
            last_name=validated_data.get('last_name'),
        )

        civilian_role, _ = Role.objects.get_or_create(
            name='Civilian',
            defaults={
                'access_level': 0,
                'description': 'Standard civilian user',
            }
        )

        user.roles.add(civilian_role)
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    email = serializers.EmailField(required=False)
    national_id = serializers.CharField(required=False)
    phone_number = serializers.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[self.username_field].required = False

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['username'] = user.username
        token['roles'] = list(user.roles.values_list('name', flat=True))
        token['highest_access_level'] = user.highest_access_level

        return token

    def validate(self, attrs):
        password = attrs.get('password')

        username_input = attrs.get('username')
        email_input = attrs.get('email')
        national_id_input = attrs.get('national_id')
        phone_number_input = attrs.get('phone_number')

        if not password:
            raise exceptions.ValidationError('Password is required.')

        user = None

        if email_input:
            user = User.objects.filter(email__iexact=email_input).first()
        elif national_id_input:
            user = User.objects.filter(national_id=national_id_input).first()
        elif phone_number_input:
            user = User.objects.filter(phone_number=phone_number_input).first()
        elif username_input:
            user = User.objects.filter(username__iexact=username_input).first()
        else:
            raise exceptions.ValidationError(
                'You must provide a username, email, national_id, or phone_number.'
            )

        if user and user.check_password(password):
            if not user.is_active:
                raise exceptions.AuthenticationFailed('User account is disabled.')

            token = self.get_token(user)

            data = {
                'refresh': str(token),
                'access': str(token.access_token),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': getattr(user, 'email', ''),
                    'national_id': getattr(user, 'national_id', ''),
                    'phone_number': getattr(user, 'phone_number', ''),
                    'roles': list(user.roles.values_list('name', flat=True)),
                    'highest_access_level': user.highest_access_level,
                }
            }

            return data

        raise exceptions.AuthenticationFailed('No active account found with the given credentials.')


class RoleRequestSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    requested_role_name = serializers.CharField(source='requested_role.name', read_only=True)

    class Meta:
        model = RoleRequest
        fields = [
            'id', 'user', 'user_name', 'requested_role', 'requested_role_name',
            'reason', 'status', 'created_at', 'reviewed_by', 'reviewed_at'
        ]
        read_only_fields = ['id', 'user', 'status', 'created_at', 'reviewed_by', 'reviewed_at']

    def validate(self, attrs):
        request = self.context.get('request')
        requested_role = attrs.get('requested_role')

        if request.user.roles.filter(id=requested_role.id).exists():
            raise serializers.ValidationError({"requested_role": "You already have this role."})

        if RoleRequest.objects.filter(user=request.user, requested_role=requested_role, status='pending').exists():
            raise serializers.ValidationError({"requested_role": "You already have a pending request for this role."})

        return attrs

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ProcessRoleRequestSerializer(serializers.Serializer):
    action = serializers.ChoiceField(
        choices=['approve', 'reject'],
        help_text="Type 'approve' to grant the role, or 'reject' to deny it."
    )
