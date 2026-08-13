from rest_framework.permissions import BasePermission, IsAuthenticated


class CanViewAuditLogsPermission(IsAuthenticated):
    """
    Проверяет, что пользователь авторизован в системе.
    Дополнительная ролевая фильтрация записей производится внутри AuditSelector.
    """
    pass