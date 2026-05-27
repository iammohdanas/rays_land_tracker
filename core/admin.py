from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import (
    Project,
    SubStageDocument,
    WorkflowStage,
    WorkflowSubStage,
    WorkflowApproval,
    WorkflowAuditLog
)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code', 'location', 'capacity_mw', 'is_active')
    search_fields = ('name', 'code', 'location')
    list_filter = ('is_active',)
    ordering = ('-created_at',)


@admin.register(WorkflowStage)
class WorkflowStageAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'project', 'sequence', 'approved')
    search_fields = ('title', 'stage_code', 'project__name')
    list_filter = ('approved',)
    ordering = ('sequence',)


@admin.register(WorkflowSubStage)
class WorkflowSubStageAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'substage_code',
        'title',
        'stage',
        'sequence',
        'approved',
        'is_completed'
    )

    search_fields = (
        'substage_code',
        'title',
        'stage__title'
    )

    list_filter = (
        'approved',
        'is_completed'
    )

    ordering = ('sequence',)


@admin.register(WorkflowApproval)
class WorkflowApprovalAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'substage',
        'approver_name',
        'approval_level',
        'status'
    )

    search_fields = (
        'approver_name',
        'substage__title'
    )

    list_filter = (
        'status',
    )

    ordering = ('approval_level',)


@admin.register(WorkflowAuditLog)
class WorkflowAuditLogAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'project',
        'action_type',
        'triggered_by',
        'created_at'
    )

    search_fields = (
        'project__name',
        'action_type',
        'triggered_by'
    )

    list_filter = (
        'action_type',
    )

    ordering = ('-created_at',)
    

@admin.register(SubStageDocument)
class SubStageDocumentAdmin(admin.ModelAdmin):
    list_display = [field.name for field in SubStageDocument._meta.fields]