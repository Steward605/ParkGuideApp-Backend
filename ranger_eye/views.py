from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.core.files.base import ContentFile
from django.utils import timezone

from .models import RangerEyeAlert, RangerEyeRecording, RangerEyeRecorderStatus


def make_alert_id():
    next_number = RangerEyeAlert.objects.count() + 1
    return f"RE-{next_number:04d}"


def serialize_alert(alert):
    return {
        "id": alert.id,
        "alert_id": alert.alert_id,
        "event_type": alert.event_type,
        "time": alert.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "status": alert.get_status_display(),
        "source": alert.source,
        "device_id": alert.device_id,
        "location": alert.location,
        "message": alert.message,
        "filename": alert.evidence_image.name.split("/")[-1] if alert.evidence_image else None,
        "image_url": alert.evidence_image.url if alert.evidence_image else None,
    }


def serialize_recording(recording):
    return {
        "id": recording.id,
        "filename": recording.filename,
        "time": recording.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "duration": recording.duration_seconds,
        "source": recording.source,
        "video_url": recording.video_file.url if recording.video_file else None,
    }


def get_recorder_status():
    status, _ = RangerEyeRecorderStatus.objects.get_or_create(pk=1)
    return status


@require_GET
def dashboard_data(request):
    alerts = RangerEyeAlert.objects.all()[:50]
    recordings = RangerEyeRecording.objects.all()[:20]
    recorder_status = get_recorder_status()

    pending_count = RangerEyeAlert.objects.filter(
        status=RangerEyeAlert.STATUS_PENDING
    ).count()

    evidence_count = RangerEyeAlert.objects.exclude(
        evidence_image=""
    ).exclude(
        evidence_image__isnull=True
    ).count()

    return JsonResponse({
        "total_alerts": RangerEyeAlert.objects.count(),
        "pending_count": pending_count,
        "evidence_count": evidence_count,
        "alerts": [serialize_alert(alert) for alert in alerts],
        "recordings": [serialize_recording(recording) for recording in recordings],
        "recording_count": RangerEyeRecording.objects.count(),
        "recording_status": {
            "running": recorder_status.running,
            "last_recording": recorder_status.last_recording,
            "next_recording": recorder_status.next_recording,
            "message": recorder_status.message,
        },
    })


@csrf_exempt
@require_POST
def upload_evidence(request):
    image_data = request.body

    if not image_data:
        return JsonResponse({"detail": "No image received."}, status=400)

    alert_type = request.GET.get("type", "manual")

    if alert_type == "manual":
        event_type = "Manual Ranger Evidence Alert"
    elif alert_type == "sound":
        event_type = "Automatic Sound Evidence Alert"
    else:
        event_type = "Camera Evidence Alert"

    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    filename = f"evidence_{alert_type}_{timestamp}.jpg"

    alert = RangerEyeAlert.objects.create(
        alert_id=make_alert_id(),
        event_type=event_type,
        status=RangerEyeAlert.STATUS_PENDING,
        source="ESP32-CAM",
        device_id="RE-CAM-01",
        location="Guided Tour Route",
        message="Photo evidence captured by wearable camera button.",
    )

    alert.evidence_image.save(filename, ContentFile(image_data), save=True)

    return JsonResponse({
        "detail": "Evidence uploaded successfully.",
        "alert": serialize_alert(alert),
    }, status=201)


@csrf_exempt
@require_POST
def sensor_alert(request):
    alert_type = request.GET.get("type", "sensor")
    location = request.GET.get("location", "Protected Plant Zone")
    message = request.body.decode("utf-8") if request.body else ""

    if alert_type == "plant_disturbance":
        event_type = "Possible Plant Disturbance Detected"
        device_id = "PLANT-SENSOR-01"
    elif alert_type == "sound_disturbance":
        event_type = "Abnormal Sound Near Protected Plant"
        device_id = "SOUND-SENSOR-01"
    elif alert_type == "node_disturbance":
        event_type = "Sensor Node Disturbance Alert"
        device_id = "MPU6050-TILT-01"
    elif alert_type == "theft_alert":
        event_type = "Sensor Node Theft / Shake Alert"
        device_id = "MPU6050-SHAKE-01"
    elif alert_type == "restricted_zone":
        event_type = "Restricted Zone Activity Detected"
        device_id = "ZONE-SENSOR-01"
    else:
        event_type = "Sensor Alert"
        device_id = "SENSOR-NODE-01"

    alert = RangerEyeAlert.objects.create(
        alert_id=make_alert_id(),
        event_type=event_type,
        status=RangerEyeAlert.STATUS_PENDING,
        source="ESP32 Sensor Node",
        device_id=device_id,
        location=location.replace("_", " "),
        message=message,
    )

    return JsonResponse({
        "detail": "Sensor alert received.",
        "alert": serialize_alert(alert),
    }, status=201)

@csrf_exempt
@require_POST
def delete_recording(request, recording_id):
    recording = RangerEyeRecording.objects.filter(id=recording_id).first()

    if not recording:
        return JsonResponse({"detail": "Recording not found."}, status=404)

    video_name = recording.filename

    if recording.video_file:
        recording.video_file.delete(save=False)

    recording.delete()

    return JsonResponse({
        "detail": f"Recording deleted: {video_name}"
    }, status=200)