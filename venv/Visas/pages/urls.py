from django.urls import path
from . import views

urlpatterns = [
    path('visas/', views.visas, name='visas')
]