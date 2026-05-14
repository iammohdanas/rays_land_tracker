
from django.urls import include, path
from . import views

urlpatterns = [
    path('', views.index, name='main'),
    path('home/', views.index, name='home')
    ]