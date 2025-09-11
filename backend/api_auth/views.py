from rest_framework_simplejwt import views as jwt
from rest_framework_simplejwt import serializers as jwt_serializer
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status


@extend_schema_view(
    post=extend_schema(
        summary="Obtain JWT Token",
        description="Use this endpoint to obtain a JWT token by providing valid credentials.",
        responses={
            status.HTTP_200_OK: jwt_serializer.TokenObtainPairSerializer,
            status.HTTP_401_UNAUTHORIZED: "Invalid credentials provided."
        }
    )
)
class BasicAuthView(jwt.TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class BasicAuthRefreshView(jwt.TokenRefreshView):
    pass

class BasicAuthVerifyView(jwt.TokenVerifyView):
    pass