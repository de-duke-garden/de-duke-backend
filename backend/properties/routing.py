from django.urls import re_path, path

from . import consumers


websocket_urlpatterns = [
    # re_path(r"ws/chat/(?P<payload>\w+)/$", consumers.ChatConsumer.as_asgi()),
    path("ws/chat/<str:payload>/", consumers.ChatConsumer.as_asgi()),
]