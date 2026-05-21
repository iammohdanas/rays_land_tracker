from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from authenticator.decorators import admin_required, role_required
from core.models import Project, WorkflowStage
from core.utils.blueprint_loader import load_workflow_blueprint
from django.contrib.auth.decorators import login_required


def index(request):
    return render(request, "index.html")


def sop_workflow(request):
    return render(request, "pages/sop_workflow.html")


@login_required
@admin_required
@role_required(['admin', 'manager'])
def create_project_page(request):
    return render(request, "pages/create_project.html")


@login_required
@admin_required
@role_required(['admin', 'manager'])
def project_list_page(request):
    return render(request, "pages/project_list.html")


@login_required
@admin_required
@role_required(['admin', 'manager'])
def workflow_page(request, project_id):
    project = get_object_or_404(Project, project_id=project_id)
    return render(request, "pages/sop_workflow.html", {"project": project})

@login_required
@admin_required
@role_required(['admin', 'manager'])
def stage_detail_page(request, project_id, stage_id):
    project = get_object_or_404(Project, project_id=project_id)
    stage = get_object_or_404(WorkflowStage, stage_id=stage_id, project=project)
    print(f"Stage ID: {stage_id}, Stage Name: {stage}, Project ID: {project_id}")
    return render(
        request, "pages/stage_detail.html", {"project": project, "stage": stage}
    )
