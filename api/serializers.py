import os

from rest_framework import serializers
from core.models import (
    Project,
    SubStageDocument,
    WorkflowStage,
    WorkflowSubStage,
    WorkflowApproval,
)


class ProjectListSerializer(serializers.ModelSerializer):
    view_url = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "name",
            "code",
            "project_id",
            "location",
            "capacity_mw",
            "created_at",
            "view_url",
        ]

    def get_view_url(self, obj):
        return f"/projects/{obj.project_id}/"


class WorkflowApprovalSerializer(serializers.ModelSerializer):

    class Meta:
        model = WorkflowApproval

        fields = ["id", "approver_name", "approval_level", "status", "remarks"]


class SubStageDocumentSerializer(serializers.ModelSerializer):

    document_name = serializers.SerializerMethodField()
    document_url = serializers.SerializerMethodField()

    class Meta:

        model = SubStageDocument

        fields = [
            "id",
            "title",
            "description",
            "remarks",
            "document_type",
            "document_name",
            "document_url",
            "uploaded_by",
            "version",
            "verification_status",
            "ai_verification_score",
            "ai_summary",
            "tags",
            "created_at",
        ]

    def get_document_name(self, obj):

        return os.path.basename(obj.document.name)

    def get_document_url(self, obj):

        request = self.context.get("request")

        if request:
            return request.build_absolute_uri(obj.document.url)

        return obj.document.url


class WorkflowSubStageSerializer(serializers.ModelSerializer):

    approvals = serializers.SerializerMethodField()
    documents = SubStageDocumentSerializer(many=True, read_only=True)

    class Meta:

        model = WorkflowSubStage

        fields = [
            "id",
            "substage_id",
            "substage_code",
            "title",
            "assigned_role",
            "duration",
            "sequence",
            "is_completed",
            "remarks",
            "metadata",
            "created_at",
            "updated_at",
            "documents",
            "approvals",
        ]

    def get_approvals(self, obj):

        approval_dict = {}

        approvals = obj.approval_matrix.all().order_by("approval_level")

        for approval in approvals:

            approval_dict[approval.approver_name] = {
                "status": approval.status,
                "remarks": approval.remarks,
                "approved_at": approval.approved_at,
                "approval_level": approval.approval_level,
            }

        return approval_dict


class WorkflowStageSerializer(serializers.ModelSerializer):
    substages = WorkflowSubStageSerializer(many=True)
    class Meta:
        model = WorkflowStage
        fields = [
            "id",
            "stage_id",
            "stage_code",
            "title",
            "sequence",
            "substages",
        ]
