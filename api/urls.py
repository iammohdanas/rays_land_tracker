from django.urls import path
from . import views

urlpatterns = [
    path("create-project/", views.create_project_api, name="create_project_api"),
    path("workflow-blueprint/",views.workflow_blueprint_api, name="workflow_blueprint_api"),
    path("projects/", views.project_list_api, name="project_list_api"),
    path("workflow/<str:project_id>/", views.workflow_data_api, name="workflow_data_api"),
]
