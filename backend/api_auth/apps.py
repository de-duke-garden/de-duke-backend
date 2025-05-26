from django.apps import AppConfig


class ApiAuthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api_auth'

    def ready(self):
        # Import the authentication module to ensure it's loaded
        # when the app is ready.
        # import api_auth.authentication
        import firebase_admin
        from firebase_admin import credentials
        import os
        from django.conf import settings

        FIREBASE_CRED_DIR = settings.FIREBASE_CRED_DIR
        FIREBASE_CRED_FILE = settings.FIREBASE_CRED_FILE

        if not firebase_admin._apps:
            # Initialize Firebase Admin SDK only if it hasn't been initialized yet
            # This prevents the error "Already initialized" when running tests
            # or when the settings are loaded multiple times
            # Initialize the app with a service account, granting admin privileges
            if FIREBASE_CRED_DIR and FIREBASE_CRED_FILE:
                print(f"Initializing Firebase Admin SDK with credentials from {FIREBASE_CRED_DIR}/{FIREBASE_CRED_FILE}")
                firebase_admin.initialize_app(
                    credentials.Certificate(os.path.join(FIREBASE_CRED_DIR, FIREBASE_CRED_FILE))
                )
