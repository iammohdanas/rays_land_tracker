from rest_framework import serializers
from core.models import Project


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
