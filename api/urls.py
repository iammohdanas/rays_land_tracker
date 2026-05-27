from django.urls import path
from django.conf import settings
from rays_land_tracker import settings
from . import views

urlpatterns = [
    path("create-project/", views.create_project_api, name="create_project_api"),
    path("workflow-blueprint/",views.workflow_blueprint_api, name="workflow_blueprint_api"),
    path("projects/", views.project_list_api, name="project_list_api"),
    path("workflow/<str:project_id>/", views.workflow_data_api, name="workflow_data_api"),
    path("substages/<str:substage_id>/upload-document/", views.upload_substage_document, name="upload-substage-document"),
    path("documents/<int:document_id>/verify/", views.verify_substage_document, name="verify-substage-document"),
    # urls.py

path(
    "compare-documents/",
    views.compare_documents_api,
    name="compare_documents_api"
),    
]
