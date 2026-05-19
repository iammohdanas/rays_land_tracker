from django.http import JsonResponse
from django.shortcuts import render

from core.utils.blueprint_loader import load_workflow_blueprint

def index(request):
    return render(request, 'index.html')


def sop_workflow(request):
    return render(request, 'pages/sop_workflow.html')


def create_project_page(request):
    return render(request, 'pages/create_project.html')


def project_list_page(request):
    return render(request, 'pages/project_list.html')