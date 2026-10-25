from django.contrib import admin
from django.urls import path
from chatbot import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.index, name="index"),
    path("chat_with_ai/", views.chat_with_ai, name="chat_with_ai"),
    path("process_audio/", views.process_audio, name="process_audio"),
    path("text_to_speech/", views.text_to_speech, name="text_to_speech"),
]
