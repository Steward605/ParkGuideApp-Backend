from django.urls import path
from .views import dashboard_data, upload_evidence, sensor_alert, sensor_telemetry, delete_recording

urlpatterns = [
    path("dashboard-data/", dashboard_data, name="ranger_eye_dashboard_data"),
    path("upload/", upload_evidence, name="ranger_eye_upload_evidence"),
    path("sensor-telemetry/", sensor_telemetry, name="ranger_eye_sensor_telemetry"),
    path("sensor-alert/", sensor_alert, name="ranger_eye_sensor_alert"),
    path("recordings/<int:recording_id>/delete/", delete_recording, name="ranger_eye_delete_recording"),
]
