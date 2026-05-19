
from django.urls import include, path
from . import views

urlpatterns = [
    path('', views.index, name='main'),
    path('home/', views.index, name='home'),
    path('sop-workflow/', views.sop_workflow, name='sop_workflow'),
    path('create-project/', views.create_project_page, name='create_project'),
    path('projects/', views.project_list_page, name='project_list'),
    ]