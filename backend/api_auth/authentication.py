from firebase_admin import auth as firebase_auth
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import authentication, exceptions
from rest_framework.authentication import get_authorization_header
from django.db.models import Q
import logging

logger = logging.getLogger("django")


class FirebaseAuthentication(authentication.BaseAuthentication):
    """
    An authentication plugin that authenticates requests through a Firebase
    token provided in a request header.
    """

    www_authenticate_realm = "api"
    media_type = "application/json"

    def authenticate(self, request):
        header = get_authorization_header(request).split()
        
        if not header or header[0].lower() != b"bearer":
            return None

        if len(header) == 1:
            raise exceptions.AuthenticationFailed(_("Invalid token header. No credentials provided."))
        elif len(header) > 2:
            raise exceptions.AuthenticationFailed(_("Invalid token header. Token string should not contain spaces."))

        try:
            token = header[1].decode()
            decoded_token = firebase_auth.verify_id_token(token, clock_skew_seconds=60)
            uid = decoded_token["uid"]
        except Exception as e:
            logger.error(f"Firebase token verification failed: {e}")
            return None # Let other authentication classes handle the request

        User = get_user_model()
        try:
            user = User.objects.get(Q(firebase_uid=uid) | Q(email=decoded_token.get("email")))
            if not user.firebase_uid or not user.email_verified:
                # If the user exists but does not have a firebase_uid, update it
                # and set email_verified to True
                user.firebase_uid = uid
                user.email_verified = True
                user.save()
        except User.DoesNotExist:
            # If the user does not exist, create a new user instance
            email = decoded_token.get("email")
            display_name: str = decoded_token.get("name")
            first_name, last_name = display_name.split(" ", 1) if display_name else (None, None)
            user = User(email=email, first_name=first_name, last_name=last_name, firebase_uid=uid)
            user.email_verified = True  # Assuming the email is verified by Firebase
            user.save()
            # TODO: Send a welcome email or perform any other action if needed
        except Exception as e:
            logger.error(f"Error retrieving user: {e}")
            raise exceptions.AuthenticationFailed(_("User retrieval failed.")) from e

        return (user, None)