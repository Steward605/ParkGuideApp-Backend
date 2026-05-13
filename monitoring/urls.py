from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import MonitorClipViewSet, MonitorEsp32FirebaseFramesProcessView, MonitorEsp32FrameUploadSessionView, MonitorEsp32FramesUploadView, MonitorEsp32RecordView, MonitorEvidenceUploadView, MonitorSessionStartView, MonitorSessionStopView, MonitorStatusView, ViolationAlertViewSet

router = DefaultRouter()
router.register(r"alerts", ViolationAlertViewSet, basename="monitor-alert")
router.register(r"clips", MonitorClipViewSet, basename="monitor-clip")

urlpatterns = [
    path("status/", MonitorStatusView.as_view()),
    path("session/start/", MonitorSessionStartView.as_view()),
    path("session/stop/", MonitorSessionStopView.as_view()),
    path("esp32/record/", MonitorEsp32RecordView.as_view()),
    path("esp32/frames/", MonitorEsp32FramesUploadView.as_view()),
    path("esp32/frame-upload-session/", MonitorEsp32FrameUploadSessionView.as_view()),
    path("esp32/process-firebase-frames/", MonitorEsp32FirebaseFramesProcessView.as_view()),
    path("evidence/", MonitorEvidenceUploadView.as_view()),
    path("", include(router.urls)),
]
