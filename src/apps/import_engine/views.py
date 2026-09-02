import json
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from apps.import_engine.services import create_preview_project

def import_wizard(request):
    return render(request, 'import_engine/import_wizard.html')

def upload_and_preview(request):
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        # Вызов транзакционного сервиса из Этапа 1
        preview_data = create_preview_project(actor=request.user, file=uploaded_file)
        
        return render(request, 'import_engine/partials/preview_project.html', {
            'preview_data': preview_data
        })
    return HttpResponse("Ошибка загрузки файла", status=400)

def confirm_project(request):
    if request.method == 'POST':
        # Здесь будет логика Этапа 3: сохранение проверенных данных в БД
        return JsonResponse({"status": "success", "message": "Проект успешно создан!"})