from rest_framework import viewsets
from rest_framework import permissions
from utilities.email import EmailDispatcher
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework import views, permissions, status, parsers
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.request import Request
from django_ratelimit.decorators import ratelimit
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, viewsets
from django.contrib.auth import get_user_model
from .models import OTPRequest, StakeholderAccount
from .serializers import BecomeAStakeholderSerializer, PhoneNumberSerializer, ResetPasswordWithTokenSerializer, UserCreateSerializer
from .serializers import UserSerializer, UserMeSerializer, ChangeAccountPasswordSerializer, VerifyEmailSerializer
from .serializers import SendOTPSerializer, VerifyOTPSerializer, ResetPasswordSerializer
import logging
import jwt
from django.conf import settings


logger = logging.getLogger("django")

User = get_user_model()


@extend_schema_view(
    signup=extend_schema(
        summary="Sign Up",
        description="Create a new user account.",
        request=UserCreateSerializer,
        responses={
            status.HTTP_201_CREATED: UserCreateSerializer,
            status.HTTP_400_BAD_REQUEST: None,
        }
    )
)
class UserViewSet(viewsets.mixins.ListModelMixin,
                  viewsets.mixins.RetrieveModelMixin,
                  viewsets.GenericViewSet):
    queryset = User.objects.all()
    lookup_field = 'pk'
    lookup_url_kwarg = 'pk'
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    @action(methods=['POST'], detail=False, url_path='signup')
    def signup(self, request: Request, *args, **kwargs):
        """
        Sign up a new user.
        """
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Create a new user instance without saving it yet
            user = User(**serializer.validated_data)
            # Hash the password
            user.set_password(serializer.validated_data['password'])
            # Save the user to the database
            user.save()
            return Response(UserCreateSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    change_password=extend_schema(
        summary="Change Password",
        description="Change the password of the authenticated user.",
        request=ChangeAccountPasswordSerializer,
        responses={
            status.HTTP_200_OK: None,
            status.HTTP_400_BAD_REQUEST: None,
            status.HTTP_406_NOT_ACCEPTABLE: None,
        }
    ),
    get_profile=extend_schema(
        summary="Get Profile",
        description="Get the profile of the authenticated user.",
        responses={
            status.HTTP_200_OK: UserMeSerializer,
        }
    ),
    update_profile=extend_schema(
        summary="Update Profile",
        description="Update the profile of the authenticated user.",
        request=UserMeSerializer,
        responses={
            status.HTTP_200_OK: UserMeSerializer,
            status.HTTP_400_BAD_REQUEST: None,
        }
    ),
    add_phone_number=extend_schema(
        summary="Add Phone Number",
        description="Add a phone number to the authenticated user.",
        request=PhoneNumberSerializer,
        responses={
            status.HTTP_200_OK: PhoneNumberSerializer,
            status.HTTP_400_BAD_REQUEST: None,
        }
    ),
    become_stakeholder=extend_schema(
        summary="Become Stakeholder",
        description="Become a stakeholder by providing identity details.",
        request=BecomeAStakeholderSerializer,
        responses={
            status.HTTP_201_CREATED: None,
            status.HTTP_400_BAD_REQUEST: None,
            status.HTTP_404_NOT_FOUND: None,
        }
    )
)
class UserMeViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    lookup_field = 'pk'
    lookup_url_kwarg = 'pk'
    # serializer_class = UserMeSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.JSONParser, parsers.MultiPartParser]

    def get_serializer_class(self):
        if self.action in ['get_profile', 'update_profile']:
            return UserMeSerializer
        elif self.action == 'add_phone_number':
            return PhoneNumberSerializer
        elif self.action == 'become_stakeholder':
            return BecomeAStakeholderSerializer
        elif self.action == 'change_password':
            return ChangeAccountPasswordSerializer
        return UserMeSerializer

    @action(methods=['POST'], detail=False, url_path='change-password')
    def change_password(self, request: Request, *args, **kwargs):
        """
        Change the password of the authenticated user.
        """
        user = request.user
        serializer = ChangeAccountPasswordSerializer(
            data=request.data)
        if serializer.is_valid():
            old_password = serializer.validated_data.get('old_password')
            new_password = serializer.validated_data.get('new_password')
            if user.check_password(old_password):
                user.set_password(new_password)
                user.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response({
                "detail": "The old password is not correct"
            }, status=status.HTTP_406_NOT_ACCEPTABLE)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(methods=['GET'], detail=False, url_path='profile')
    def get_profile(self, request: Request, *args, **kwargs):
        """
        Get the profile of the authenticated user.
        """
        user = request.user
        serializer = UserMeSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(methods=['PATCH'], detail=False, url_path='update-profile')
    def update_profile(self, request: Request, *args, **kwargs):
        """
        Update the profile of the authenticated user.
        """
        user = request.user
        serializer = UserMeSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(methods=['POST'], detail=False, url_path='add-phone-number')
    def add_phone_number(self, request: Request, *args, **kwargs):
        """
        Add a phone number to the authenticated user.
        """
        user = request.user
        serializer = PhoneNumberSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user.phone_number.mobile = serializer.validated_data['mobile']
                user.phone_number.is_verified = False
                user.phone_number.save()
            except User.phone_number.RelatedObjectDoesNotExist:
                serializer.save(user=user)

            return Response(PhoneNumberSerializer(user.phone_number).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(methods=['POST'], detail=False, url_path='become-stakeholder', )
    def become_stakeholder(self, request: Request, *args, **kwargs):
        """
        Become a stakeholder by providing identity details.
        """
        try:
            user = request.user
            serializer = BecomeAStakeholderSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=user)
            return Response({'detail': 'Stakeholder account created successfully'
                         }, status=status.HTTP_201_CREATED)
        except User.stakeholder_account.RelatedObjectDoesNotExist:
            return Response({'detail': 'Stakeholder account already exists'}, status=status.HTTP_400_BAD_REQUEST)




@extend_schema_view(
    send_otp=extend_schema(
        summary="Send OTP for Password Reset",
        description="Send an OTP to the user's email address for password reset.",
        request=SendOTPSerializer,
        responses={
            status.HTTP_200_OK: None,
            status.HTTP_404_NOT_FOUND: None,
            status.HTTP_500_INTERNAL_SERVER_ERROR: None,
        }
    ),
    verify_otp=extend_schema(
        summary="Verify OTP for Password Reset",
        description="Verify the OTP sent to the user's email address for password reset.",
        request=VerifyOTPSerializer,
        responses={
            status.HTTP_200_OK: None,
            status.HTTP_400_BAD_REQUEST: None,
        }
    ),
    reset_password=extend_schema(
        summary="Reset Password",
        description="Reset the user's password using the OTP sent to their email address.",
        request=ResetPasswordSerializer,
        responses={
            status.HTTP_200_OK: None,
            status.HTTP_400_BAD_REQUEST: None,
            status.HTTP_404_NOT_FOUND: None,
        }
    ),
    reset_password_with_token=extend_schema(
        summary="Reset Password with Token",
        description="Reset the user's password using a JWT token.",
        request=ResetPasswordWithTokenSerializer,
        responses={
            status.HTTP_200_OK: None,
            status.HTTP_400_BAD_REQUEST: None,
            status.HTTP_404_NOT_FOUND: None,
        }
    )
)
class PasswordResetViewSet(viewsets.ViewSet):
    __ID_FOR = 'password-reset'
    def __ratelimit_key(group, self: 'PasswordResetViewSet'):
        request: Request = self.request
        return request.data.get('email')
    
    def __get_ref(self, input: str) -> str:
        """
        Generate a reference string for the OTP request.
        """
        return f"{self.__ID_FOR}:{input}"

    @action(detail=False, methods=['POST'])
    @ratelimit(key=__ratelimit_key, rate='3/10m')
    def send_otp(self, request: Request):
        """
        Send an OTP to the user's email address.
        This endpoint is rate-limited to 3 requests per 10 minutes.
        """
        serializer = SendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({'detail': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        otp = OTPRequest.generate_otp()
        device_hashed_token, device_plain_token = OTPRequest.generate_device_token()
        OTPRequest.objects.create(
            ref=self.__get_ref(email), otp=otp, device_identity=device_hashed_token)
        # Prepare web data
        web_data = {
            'email': email,
            'otp': otp,
            'device_identity': device_plain_token
        }
        # Encode web_data into a JWT token
        web_data_jwt = jwt.encode(
            web_data, settings.SECRET_KEY, algorithm='HS256')

        # Generate the reset password URL with the JWT token as a query parameter
        web_data_url = f"{getattr(settings, 'FRONTEND_PASSWORD_RESET_URL', '')}/?token={web_data_jwt}"

        try:
            # Send the email with the otp and reset password URL
            EmailDispatcher.reset_password_otp(
                otp=otp,
                email=email,
                web_data_url=web_data_url if getattr(settings, 'FRONTEND_PASSWORD_RESET_URL', None) else None,
            )
        except Exception as e:
            # Log the error
            logger.error(f"Error sending OTP: {e}")
            # TODO: Log this error to a logging monitoring system
            return Response({'detail': 'Failed to send OTP'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'detail': {'message': 'OTP sent successfully', 'device_identity': device_plain_token}}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['POST'])
    @ratelimit(key=__ratelimit_key, rate='5/10m')
    def verify_otp(self, request):
        """
        Verify the OTP sent to the user's email address.
        This endpoint is rate-limited to 5 requests per 10 minutes.
        """
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        device_identity = serializer.validated_data['device_identity']

        otp_entry = OTPRequest.objects.filter(
            ref=self.__get_ref(email), otp=otp).order_by('-created_at').first()
        if not otp_entry or not otp_entry.is_valid(device_identity):
            return Response({'detail': 'Invalid or expired OTP'}, status=status.HTTP_400_BAD_REQUEST)

        otp_entry.is_verified = True
        otp_entry.save()
        return Response({'detail': 'OTP verified'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['POST'])
    def reset_password(self, request):
        """
        Reset the user's password using the OTP sent to their email address.
        """
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        new_password = serializer.validated_data['new_password']
        device_identity = serializer.validated_data['device_identity']

        otp_entry = OTPRequest.objects.filter(
            ref=self.__get_ref(email), is_verified=True).order_by('-created_at').first()
        if not otp_entry or not otp_entry.is_valid(device_identity) and otp_entry.is_verified:
            return Response({'detail': 'OTP not verified or expired'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({'detail': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        user.set_password(new_password)
        user.save()

        OTPRequest.objects.filter(ref=self.__get_ref(email)).delete()

        return Response({'detail': 'Password reset successful'}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['POST'])
    def reset_password_with_token(self, request):
        """
        Reset the user's password using a JWT token.
        """
        serializer = ResetPasswordWithTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            email = payload.get('email')
            otp = payload.get('otp')
            device_identity = payload.get('device_identity')
        except jwt.ExpiredSignatureError:
            return Response({'detail': 'Token has expired'}, status=status.HTTP_400_BAD_REQUEST)
        except jwt.InvalidTokenError:
            return Response({'detail': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
        
        otp_entry = OTPRequest.objects.filter(
            ref=self.__get_ref(email), otp=otp).order_by('-created_at').first()
        if not otp_entry or not otp_entry.is_valid(device_identity):
            return Response({'detail': 'Invalid or expired OTP'}, status=status.HTTP_400_BAD_REQUEST)
        otp_entry.is_verified = True
        otp_entry.save()

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({'detail': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        user.set_password(new_password)
        user.save()

        OTPRequest.objects.filter(ref=self.__get_ref(email)).delete()

        return Response({'detail': 'Password reset successful'}, status=status.HTTP_200_OK)



@extend_schema_view(
    send_otp=extend_schema(
        summary="Send OTP for Email Verification",
        description="Send an OTP to the user's email address for verification.",
        request=SendOTPSerializer,
        responses={
            status.HTTP_200_OK: None,
            status.HTTP_404_NOT_FOUND: None,
            status.HTTP_500_INTERNAL_SERVER_ERROR: None,
        }
    ),
    verify_otp=extend_schema(
        summary="Verify OTP for Email Verification",
        description="Verify the OTP sent to the user's email address for verification.",
        request=VerifyOTPSerializer,
        responses={
            status.HTTP_200_OK: None,
            status.HTTP_400_BAD_REQUEST: None,
        }
    ),
    verify_email=extend_schema(
        summary="Verify Email Address",
        description="Verify the user's email address using the OTP sent to their email.",
        request=VerifyEmailSerializer,
        responses={
            status.HTTP_200_OK: None,
            status.HTTP_400_BAD_REQUEST: None,
            status.HTTP_404_NOT_FOUND: None,
        }
    )
)
class EmailVerificationViewSet(viewsets.ViewSet):
    __ID_FOR = 'email-verification'
    def __ratelimit_key(group, self: 'EmailVerificationViewSet'):
        request: Request = self.request
        return request.data.get('email')
    
    def __get_ref(self, input: str) -> str:
        """
        Generate a reference string for the OTP request.
        """
        return f"{self.__ID_FOR}:{input}"

    @action(detail=False, methods=['POST'])
    @ratelimit(key=__ratelimit_key, rate='3/10m')
    def send_otp(self, request: Request):
        """
        Send an OTP to the user's email address.
        This endpoint is rate-limited to 3 requests per 10 minutes.
        """
        serializer = SendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({'detail': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        otp = OTPRequest.generate_otp()
        device_hashed_token, device_plain_token = OTPRequest.generate_device_token()
        OTPRequest.objects.create(
            ref=self.__get_ref(email), otp=otp, device_identity=device_hashed_token)
        # Prepare web data
        web_data = {
            'email': email,
            'otp': otp,
            'device_identity': device_plain_token
        }
        # Encode web_data into a JWT token
        web_data_jwt = jwt.encode(
            web_data, settings.SECRET_KEY, algorithm='HS256')

        # Generate the URL with the JWT token as a query parameter
        web_data_url = f"{getattr(settings, 'FRONTEND_VERIFY_EMAIL_URL', '')}/?token={web_data_jwt}"

        try:
            # Send the email with the otp and reset password URL
            EmailDispatcher.verify_email_otp(
                otp=otp,
                email=email,
                web_data_url=web_data_url if getattr(settings, 'FRONTEND_VERIFY_EMAIL_URL', None) else None,
            )
        except Exception as e:
            # Log the error
            logger.error(f"Error sending OTP: {e}")
            # TODO: Log this error to a logging monitoring system
            return Response({'detail': 'Failed to send OTP'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'detail': {'message': 'OTP sent successfully', 'device_identity': device_plain_token}}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['POST'])
    @ratelimit(key=__ratelimit_key, rate='5/10m')
    def verify_otp(self, request):
        """
        Verify the OTP sent to the user's email address.
        This endpoint is rate-limited to 5 requests per 10 minutes.
        """
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        device_identity = serializer.validated_data['device_identity']

        otp_entry = OTPRequest.objects.filter(
            ref=self.__get_ref(email), otp=otp).order_by('-created_at').first()
        if not otp_entry or not otp_entry.is_valid(device_identity):
            return Response({'detail': 'Invalid or expired OTP'}, status=status.HTTP_400_BAD_REQUEST)

        otp_entry.is_verified = True
        otp_entry.save()
        return Response({'detail': 'OTP verified'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['POST'])
    def verify_email(self, request):
        """
        Verify user's email address.
        """
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        device_identity = serializer.validated_data['device_identity']

        otp_entry = OTPRequest.objects.filter(
            ref=self.__get_ref(email), is_verified=True).order_by('-created_at').first()
        if not otp_entry or not otp_entry.is_valid(device_identity) and otp_entry.is_verified:
            return Response({'detail': 'OTP not verified or expired'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({'detail': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        user.email_verified = True
        user.save()

        OTPRequest.objects.filter(ref=self.__get_ref(email)).delete()

        return Response({'detail': 'Email verified successfully'}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['POST'])
    def verify_email_with_token(self, request):
        """
        Verify user's email using a JWT token.
        """
        serializer = ResetPasswordWithTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data['token']

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            email = payload.get('email')
            otp = payload.get('otp')
            device_identity = payload.get('device_identity')
        except jwt.ExpiredSignatureError:
            return Response({'detail': 'Token has expired'}, status=status.HTTP_400_BAD_REQUEST)
        except jwt.InvalidTokenError:
            return Response({'detail': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
        
        otp_entry = OTPRequest.objects.filter(
            ref=self.__get_ref(email), otp=otp).order_by('-created_at').first()
        if not otp_entry or not otp_entry.is_valid(device_identity):
            return Response({'detail': 'Invalid or expired OTP'}, status=status.HTTP_400_BAD_REQUEST)
        otp_entry.is_verified = True
        otp_entry.save()

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({'detail': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        user.email_verified = True
        user.save()

        OTPRequest.objects.filter(ref=self.__get_ref(email)).delete()

        return Response({'detail': 'Email verified successfully'}, status=status.HTTP_200_OK)
