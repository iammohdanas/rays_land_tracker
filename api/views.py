import json
import random

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from api.serializers import (
    ProjectListSerializer,
    SubStageDocumentSerializer,
    WorkflowStageSerializer,
)
from core.models import Project, SubStageDocument, WorkflowStage, WorkflowSubStage
from rest_framework.decorators import api_view
from django.http import JsonResponse
import json
from django.db import transaction
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer
from core.utils.blueprint_loader import load_workflow_blueprint
from core.utils.extra_utils import generate_file_hash
import difflib
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from PyPDF2 import PdfReader
from docx import Document
from PIL import Image
import easyocr



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
    serializer = ProjectListSerializer(projects, many=True)
    return JsonResponse({"data": serializer.data})


@api_view(["GET"])
def workflow_data_api(request, project_id):
    project = get_object_or_404(Project, project_id=project_id)
    stages = (
        WorkflowStage.objects.filter(project=project)
        .prefetch_related("substages", "substages__approval_matrix")
        .order_by("sequence")
    )
    serializer = WorkflowStageSerializer(
        stages, many=True, context={"request": request}
    )
    return Response({"success": True, "data": serializer.data})


@api_view(["POST"])
@renderer_classes([JSONRenderer])
def upload_substage_document(request, substage_id):
    try:
        substage = get_object_or_404(WorkflowSubStage, substage_id=substage_id)
        uploaded_file = request.FILES.get("document")
        if not uploaded_file:
            return Response(
                {"success": False, "message": "Document file is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        document_hash = generate_file_hash(uploaded_file)
        uploaded_file.seek(0)
        existing_document = SubStageDocument.objects.filter(
            document_hash=document_hash
        ).first()
        print(
            existing_document.document_hash
            if existing_document
            else "No existing document with same hash"
        )
        if existing_document:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Duplicate document detected. " "Same document already exists."
                    ),
                    "duplicate_document": {
                        "id": existing_document.id,
                        "title": existing_document.title,
                        "substage": (existing_document.substage.title),
                        "uploaded_at": (existing_document.created_at),
                        "document_url": request.build_absolute_uri(
                            existing_document.document.url
                        ),
                    },
                },
                status=status.HTTP_409_CONFLICT,
            )
        document = SubStageDocument.objects.create(
            substage=substage,
            title=request.data.get("title"),
            description=request.data.get("description"),
            remarks=request.data.get("remarks"),
            document_type=request.data.get("document_type"),
            version=request.data.get("version", 1),
            uploaded_by=(
                request.user.username if request.user.is_authenticated else "System"
            ),
            document=uploaded_file,
            document_hash=document_hash,
        )
        serializer = SubStageDocumentSerializer(document, context={"request": request})
        return Response(
            {
                "success": True,
                "message": ("Document uploaded successfully."),
                "data": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )
    except Exception as e:
        return Response(
            {"success": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@renderer_classes([JSONRenderer])
def verify_substage_document(request, document_id):
    document = get_object_or_404(SubStageDocument, id=document_id)
    try:
        """
        FUTURE AI/LLM FLOW

        Here agent will:

        1. Read uploaded document
        2. Extract text using OCR/PDF parser
        3. Validate required fields
        4. Check signatures/stamps
        5. Match ownership/project data
        6. Generate AI summary
        7. Return confidence score
        """

        # MOCKED AI RESPONSE FOR NOW
        ai_score = round(random.uniform(82, 99), 2)
        document.ai_verification_score = ai_score
        document.ai_summary = (
            "Document appears valid. "
            "Required fields detected successfully. "
            "No major inconsistencies found."
        )
        document.ai_verification_response = {
            "status": "success",
            "validated_fields": [
                "owner_name",
                "document_id",
                "survey_number",
                "project_reference",
            ],
            "issues": [],
        }
        document.verification_status = "verified"
        document.save()
        return Response(
            {
                "success": True,
                "message": "AI verification completed.",
                "data": {
                    "document_id": document.id,
                    "ai_score": ai_score,
                    "verification_status": document.verification_status,
                },
            }
        )
    except Exception as e:
        return Response({"success": False, "message": str(e)})


# views.py



def extract_text(file):
    extension = file.name.split(".")[-1].lower()
    extracted_text = ""
    # PDF
    if extension == "pdf":
        reader = PdfReader(file)
        for page in reader.pages:
            extracted_text += page.extract_text() or ""
    # DOCX
    elif extension == "docx":
        doc = Document(file)
        for para in doc.paragraphs:
            extracted_text += para.text + "\n"
    # TXT
    elif extension == "txt":
        extracted_text = file.read().decode("utf-8")
    # IMAGE OCR
    elif extension in ["png", "jpg", "jpeg"]:
        image = Image.open(file)
        reader = easyocr.Reader(["en", "hi"])
        result = reader.readtext(image, detail=0)
        extracted_text = "\n".join(result)
    return extracted_text


@csrf_exempt
def compare_documents_api(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request method."})
    try:
        document_1 = request.FILES.get("document_1")
        document_2 = request.FILES.get("document_2")
        if not document_1 or not document_2:
            return JsonResponse(
                {"success": False, "message": "Both documents are required."}
            )
        text_1 = extract_text(document_1)
        text_2 = extract_text(document_2)
        lines_1 = text_1.splitlines()
        lines_2 = text_2.splitlines()
        differences = []
        matcher = difflib.SequenceMatcher(None, lines_1, lines_2)
        for opcode in matcher.get_opcodes():
            tag, i1, i2, j1, j2 = opcode
            if tag == "equal":
                continue
            differences.append(
                {
                    "type": tag,
                    "line": i1 + 1,
                    "original": "\n".join(lines_1[i1:i2]),
                    "updated": "\n".join(lines_2[j1:j2]),
                }
            )
        summary = f"""
            <b>Total Changes:</b> {len(differences)}<br>
            <b>Document 1 Lines:</b> {len(lines_1)}<br>
            <b>Document 2 Lines:</b> {len(lines_2)}
        """
        return JsonResponse(
            {
                "success": True,
                "summary": summary,
                "total_differences": len(differences),
                "differences": differences,
            }
        )
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})
