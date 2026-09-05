from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.exceptions import ObjectDoesNotExist

from apps.organization.models import DepartmentMembership
from apps.orders.models import Order
from apps.workflow.models import Output
from apps.assignments.models import Assignment
from apps.documents.models import Document, DocumentVersion
from django.contrib.contenttypes.models import ContentType


@login_required
def profile_page(request):
    try:
        employee = getattr(request.user, 'employee', getattr(request.user, 'employee_profile', None))
    except ObjectDoesNotExist:
        employee = None

    memberships = DepartmentMembership.objects.filter(employee=employee) if employee else []
    
    tasks = Order.objects.filter(
        executor=request.user,
        status__in=['new', 'in_progress', 'returned']
    ).select_related('project')
    
    outputs = []
    if employee:
        # ИСПРАВЛЕНО: убрали 'output__stage__project', оставили только 'output'
        active_assignments = Assignment.objects.filter(
            employee=employee,
            output__status__in=['in_progress', 'returned']
        ).select_related('output')
        outputs = [assign.output for assign in active_assignments]

    return render(request, 'accounts/profile.html', {
        'memberships': memberships,
        'tasks': tasks,
        'outputs': outputs,
    })


@login_required
@require_POST
def submit_order_from_profile(request, order_id):
    task = get_object_or_404(Order, id=order_id, executor=request.user)
    
    task.status = 'submitted'
    task.save()
    
    return render(request, 'accounts/partials/order_row.html', {'task': task})

@login_required
def attach_output_modal(request, output_id):
    """Возвращает HTML-код модального окна загрузки."""
    output = get_object_or_404(Output, id=output_id)
    return render(request, 'accounts/partials/attach_modal.html', {'output': output})

@login_required
@require_POST
def attach_output_file(request, output_id):
    """Обрабатывает загруженный файл и меняет статус Выхода НИР."""
    output = get_object_or_404(Output, id=output_id)
    file_obj = request.FILES.get('result_file')
    
    if file_obj:
        # 1. Создаем/находим корневой Документ, привязанный к Выходу НИР
        content_type = ContentType.objects.get_for_model(Output)
        doc, created = Document.objects.get_or_create(
            content_type=content_type,
            object_id=output.id,
            defaults={'name': f"Результат: {output.name}"}
        )
        
        # 2. Добавляем новую версию файла
        last_version = DocumentVersion.objects.filter(document=doc).order_by('-version_number').first()
        next_version = (last_version.version_number + 1) if last_version else 1
        
        DocumentVersion.objects.create(
            document=doc,
            file=file_obj,
            version_number=next_version,
            author=request.user
        )
        
        # 3. Меняем статус НИР на "Отправлено"
        output.status = 'submitted'
        output.save()
        
    return render(request, 'accounts/partials/output_row.html', {'output': output})