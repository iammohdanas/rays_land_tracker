import json

from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from api.serializers import ProjectListSerializer
from core.models import Project, WorkflowStage, WorkflowSubStage
from rest_framework.decorators import api_view
from django.http import JsonResponse
import json
from django.db import transaction

from core.utils.blueprint_loader import load_workflow_blueprint


def workflow_blueprint_api(request):
    return JsonResponse({"results": load_workflow_blueprint()})


from django.db import transaction, IntegrityError
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework import status


@api_view(["POST"])
@transaction.atomic
def create_project_api(request):
    try:
        payload = request.data
        if Project.objects.filter(code=payload.get("code")).exists():
            return JsonResponse(
                {"success": False, "message": "Project code already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if Project.objects.filter(project_id=payload.get("project_id")).exists():
            return JsonResponse(
                {"success": False, "message": "Project ID already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        stages_data = payload.get("stages", [])
        stage_ids = []
        substage_ids = []
        for stage in stages_data:
            stage_id = stage.get("stageId")

            if stage_id in stage_ids:
                return JsonResponse(
                    {
                        "success": False,
                        "message": f"Duplicate stage ID in payload: {stage_id}",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            stage_ids.append(stage_id)

            if WorkflowStage.objects.filter(stage_id=stage_id).exists():
                return JsonResponse(
                    {
                        "success": False,
                        "message": f"Stage ID already exists: {stage_id}",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            for substage in stage.get("substages", []):
                substage_id = substage.get("substageId")

                if substage_id in substage_ids:
                    return JsonResponse(
                        {
                            "success": False,
                            "message": f"Duplicate substage ID in payload: {substage_id}",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                substage_ids.append(substage_id)

                if WorkflowSubStage.objects.filter(substage_id=substage_id).exists():
                    return JsonResponse(
                        {
                            "success": False,
                            "message": f"Substage ID already exists: {substage_id}",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        project = Project.objects.create(
            name=payload.get("name"),
            code=payload.get("code"),
            project_id=payload.get("project_id"),
            location=payload.get("location"),
            capacity_mw=payload.get("capacity_mw"),
        )

        workflow_stages = []

        for stage_index, stage_data in enumerate(stages_data, start=1):
            workflow_stages.append(
                WorkflowStage(
                    project=project,
                    stage_id=stage_data.get("stageId"),
                    stage_code=stage_data.get(
                        "stageCode", f"STG{str(stage_index).zfill(2)}"
                    ),
                    title=stage_data.get("stageName"),
                    sequence=stage_index,
                    approved=True,
                )
            )

        created_stages = WorkflowStage.objects.bulk_create(workflow_stages)

        stage_mapping = {stage.stage_id: stage for stage in created_stages}

        workflow_substages = []

        for stage_index, stage_data in enumerate(stages_data, start=1):
            stage_instance = stage_mapping.get(stage_data.get("stageId"))

            for sub_index, substage_data in enumerate(
                stage_data.get("substages", []), start=1
            ):
                workflow_substages.append(
                    WorkflowSubStage(
                        stage=stage_instance,
                        substage_id=substage_data.get("substageId"),
                        substage_code=substage_data.get(
                            "code", f"SUB{str(sub_index).zfill(2)}"
                        ),
                        title=substage_data.get("title"),
                        assigned_role=substage_data.get("role"),
                        duration=substage_data.get("duration"),
                        sequence=sub_index,
                        approved=True,
                    )
                )

        WorkflowSubStage.objects.bulk_create(workflow_substages)

        return JsonResponse(
            {
                "success": True,
                "project_id": project.project_id,
                "message": "Project Created Successfully",
            }
        )

    except IntegrityError as error:
        transaction.set_rollback(True)

        return JsonResponse(
            {"success": False, "message": str(error)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    except Exception as error:
        transaction.set_rollback(True)

        return JsonResponse(
            {"success": False, "message": str(error)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
def project_list_api(request):
    projects = Project.objects.all()
    serializer = ProjectListSerializer(projects,many=True)

    return JsonResponse({
        "data": serializer.data
    })