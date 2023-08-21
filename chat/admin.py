from django.contrib import admin
from chat.models import ChatRoom, ChatMessage

admin.site.register(ChatRoom)
admin.site.register(ChatMessage)

