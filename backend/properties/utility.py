from django.core.signing import Signer, BadSignature
from django.conf import settings
import base64
import json
import uuid
from decimal import Decimal
from django.http import HttpRequest
from django.core.handlers.wsgi import WSGIRequest
from io import BytesIO
import urllib.parse


def encrypt_payload(payload) -> str:
    """
    Encrypt a payload dictionary using Django's signing.
    Returns the encrypted and base64 encoded string.
    """
    try:
        signer = Signer()
        signed_payload = signer.sign_object(payload)
        # Base64 encode for URL safety
        encrypted_payload = base64.urlsafe_b64encode(signed_payload.encode()).decode()
        return encrypted_payload
    except Exception as e:
        raise ValueError(f"Failed to encrypt payload: {str(e)}")

def decrypt_payload(encrypted_payload) -> dict | None:
    """
    Decrypt an encrypted payload string.
    Returns the original payload dict or None if invalid.
    """
    try:
        # Decode from base64
        signed_payload = base64.urlsafe_b64decode(encrypted_payload.encode()).decode()
        
        # Decrypt using Django's signing
        signer = Signer()
        payload = signer.unsign_object(signed_payload)
        
        return payload
    except (BadSignature, ValueError, Exception):
        return None



class JSONv2Encoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def build_request_from_scope(scope):
    """
    Build a Django-like HttpRequest object from ASGI scope.
    """

    # Create a WSGI environ dict from the ASGI scope
    environ = {
        'REQUEST_METHOD': scope.get('method', 'GET'),
        'PATH_INFO': scope['path'],
        'QUERY_STRING': scope['query_string'].decode(),
        'SERVER_NAME': scope['server'][0],
        'SERVER_PORT': str(scope['server'][1]),
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'https' if scope.get("scheme") == "wss" else 'http',
        'wsgi.input': BytesIO(b''),
        'wsgi.errors': BytesIO(),
        'wsgi.multithread': False,
        'wsgi.multiprocess': False,
        'wsgi.run_once': False,
    }

    for name, value in scope['headers']:
        name = name.decode().upper().replace('-', '_')
        if name == 'CONTENT_TYPE':
            environ['CONTENT_TYPE'] = value.decode()
        elif name == 'CONTENT_LENGTH':
            environ['CONTENT_LENGTH'] = value.decode()
        else:
            environ[f'HTTP_{name}'] = value.decode()

    request = WSGIRequest(environ)
    request.META['REMOTE_ADDR'] = scope.get('client')[0] if scope.get('client') else ''
    request.user = scope.get('user', None)
    return request