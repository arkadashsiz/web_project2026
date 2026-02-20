from rest_framework import serializers, exceptions
from django.contrib.auth import get_user_model
from .models import Role
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


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

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    # Add the optional fields so DRF recognizes them
    email = serializers.EmailField(required=False)
    national_id = serializers.CharField(required=False)
    phone_number = serializers.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make the default username field optional
        self.fields[self.username_field].required = False

    @classmethod
    def get_token(cls, user):
        # Embed custom data into the JWT payload
        token = super().get_token(user)
        token['username'] = user.username
        
        if hasattr(user, 'role') and user.role is not None:
            token['role_name'] = user.role.name
            token['access_level'] = user.role.access_level
        else:
            token['role_name'] = 'Civilian'
            token['access_level'] = 0

        return token

    def validate(self, attrs):
        password = attrs.get('password')
        
        # Extract potential identifiers
        username_input = attrs.get('username')
        email_input = attrs.get('email')
        national_id_input = attrs.get('national_id')
        phone_number_input = attrs.get('phone_number')

        if not password:
            raise exceptions.ValidationError('Password is required.')

        user = None

        # 1. Check if explicit keys were sent
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

        # 3. Verify user exists and password matches
        if user and user.check_password(password):
            if not user.is_active:
                raise exceptions.AuthenticationFailed('User account is disabled.')
            
            self.user = user
            token = self.get_token(user)
            
            # 4. Prepare the final JSON response
            data = {
                'refresh': str(token),
                'access': str(token.access_token),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': getattr(user, 'email', ''),
                    'national_id': getattr(user, 'national_id', ''),
                    'phone_number': getattr(user, 'phone_number', ''),
                }
            }

            if hasattr(user, 'role') and user.role is not None:
                data['user']['role'] = user.role.name
                data['user']['access_level'] = user.role.access_level
            else:
                data['user']['role'] = 'Civilian'
                data['user']['access_level'] = 0

            return data
            
        raise exceptions.AuthenticationFailed('No active account found with the given credentials.')