from django.db import models

from core.utils.extra_utils import substage_document_upload_path


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ApprovalBaseModel(TimeStampedModel):
    approved = models.BooleanField(default=True)

    class Meta:
        abstract = True


class Project(TimeStampedModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=100, unique=True, db_index=True)
    project_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    location = models.CharField(max_length=255)
    capacity_mw = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class WorkflowStage(ApprovalBaseModel):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="workflow_stages"
    )
    stage_id = models.CharField(
        max_length=100, unique=True, db_index=True, null=True, blank=True
    )
    stage_code = models.CharField(max_length=20)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    sequence = models.PositiveIntegerField(db_index=True)

    class Meta:
        ordering = ["sequence"]
        unique_together = ("project", "sequence")

    def __str__(self):
        return f"{self.project.code} - {self.title}"


class WorkflowSubStage(ApprovalBaseModel):
    stage = models.ForeignKey(
        WorkflowStage, on_delete=models.CASCADE, related_name="substages"
    )
    substage_id = models.CharField(
        max_length=120, unique=True, db_index=True, null=True, blank=True
    )
    substage_code = models.CharField(max_length=30, db_index=True)
    title = models.CharField(max_length=255)
    assigned_role = models.CharField(max_length=255, blank=True, null=True)
    duration = models.CharField(max_length=100, blank=True, null=True)
    sequence = models.PositiveIntegerField(db_index=True)
    is_completed = models.BooleanField(default=False)
    remarks = models.TextField(blank=True, null=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    document = models.FileField(
        upload_to="workflow/substages/documents/", blank=True, null=True
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["sequence"]
        unique_together = ("stage", "sequence")

    def __str__(self):
        return f"{self.substage_code} - {self.title}"


class WorkflowApproval(TimeStampedModel):

    class Status(models.TextChoices):
        NOT_SENT = "not_sent", "Not Sent"
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    substage = models.ForeignKey(
        WorkflowSubStage, on_delete=models.CASCADE, related_name="approval_matrix"
    )
    approver_name = models.CharField(max_length=255)
    approver_email = models.EmailField(blank=True, null=True)
    approval_level = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.NOT_SENT, db_index=True
    )
    remarks = models.TextField(blank=True, null=True)
    approved_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["approval_level"]

    def __str__(self):
        return f"{self.substage.substage_code} - {self.approver_name} ({self.status})"


class WorkflowAuditLog(TimeStampedModel):

    class Action(models.TextChoices):
        STAGE_REORDER = "stage_reorder", "Stage Reorder"
        SUBSTAGE_REORDER = "substage_reorder", "Substage Reorder"
        APPROVAL_SENT = "approval_sent", "Approval Sent"
        APPROVAL_APPROVED = "approval_approved", "Approval Approved"
        APPROVAL_REJECTED = "approval_rejected", "Approval Rejected"

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="audit_logs"
    )
    stage = models.ForeignKey(
        WorkflowStage, on_delete=models.SET_NULL, null=True, blank=True
    )
    substage = models.ForeignKey(
        WorkflowSubStage, on_delete=models.SET_NULL, null=True, blank=True
    )
    action_type = models.CharField(max_length=50, choices=Action.choices, db_index=True)
    message = models.TextField()
    previous_data = models.JSONField(default=dict, blank=True)
    new_data = models.JSONField(default=dict, blank=True)
    triggered_by = models.CharField(max_length=255, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.project.code} - {self.action_type}"


class SubStageDocument(ApprovalBaseModel):

    class VerificationStatus(models.TextChoices):

        PENDING = "pending", "Pending"
        VERIFIED = "verified", "Verified"
        REJECTED = "rejected", "Rejected"
        UNDER_REVIEW = "under_review", "Under Review"

    substage = models.ForeignKey(
        WorkflowSubStage, on_delete=models.CASCADE, related_name="documents"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    document_hash = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    remarks = models.TextField(blank=True, null=True)
    document_type = models.CharField(max_length=100, blank=True, null=True)
    document = models.FileField(upload_to=substage_document_upload_path)
    uploaded_by = models.CharField(max_length=255, blank=True, null=True)
    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    verification_status = models.CharField(
        max_length=30,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
    )
    ai_verification_score = models.FloatField(blank=True, null=True)
    ai_verification_response = models.JSONField(default=dict, blank=True)
    ai_extracted_metadata = models.JSONField(default=dict, blank=True)
    ai_summary = models.TextField(blank=True, null=True)
    tags = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-created_at"]
    def __str__(self):
        return f"{self.title} - {self.substage.substage_code}"

