from rest_framework.routers import DefaultRouter
from src.apps.audit.views import AuditViewSet

router = DefaultRouter()
router.register(r'audit', AuditViewSet, basename='audit')

urlpatterns = router.urls