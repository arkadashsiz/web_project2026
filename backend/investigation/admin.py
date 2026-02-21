from django.contrib import admin
from .models import DetectiveBoard, BoardNode, BoardEdge, Suspect, Interrogation, Notification

admin.site.register(DetectiveBoard)
admin.site.register(BoardNode)
admin.site.register(BoardEdge)
admin.site.register(Suspect)
admin.site.register(Interrogation)
admin.site.register(Notification)
