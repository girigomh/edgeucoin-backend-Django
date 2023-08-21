from django.db import models
from shortuuidfield import ShortUUIDField
from api.models import CustomUser


# Create your models here.
class ChatRoom(models.Model):
    roomId = ShortUUIDField()
    type = models.CharField(max_length=10, default="DM")
    member = models.ManyToManyField(CustomUser)
    name = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.roomId + "->" + str(self.name)


class ChatMessage(models.Model):
    chat = models.ForeignKey(ChatRoom, on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    message = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message
