from rest_framework_simplejwt import views as jwt
from rest_framework_simplejwt import serializers as jwt_serializer
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status


class BasicAuthView(jwt.TokenObtainPairView):
    @swagger_auto_schema(
        responses={
            status.HTTP_200_OK: jwt_serializer.TokenRefreshSerializer
    })
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class BasicAuthRefreshView(jwt.TokenRefreshView):
    pass

class BasicAuthVerifyView(jwt.TokenVerifyView):
    pass