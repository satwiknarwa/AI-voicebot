from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('chat_with_ai/', views.chat_with_ai, name='chat_with_ai'),
    path('process_audio/', views.process_audio, name='process_audio'),
]
