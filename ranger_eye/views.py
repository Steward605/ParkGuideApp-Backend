from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.core.files.base import ContentFile
from django.utils import timezone

from .models import RangerEyeAlert, RangerEyeRecording, RangerEyeRecorderStatus, RangerEyeSensorNode


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


def serialize_sensor_node(node):
    return {
        "id": node.id,
        "device_id": node.device_id,
        "device_name": node.device_name,
        "location": node.location,
        "ip_address": node.ip_address,
        "firmware_version": node.firmware_version,
        "soil_value": node.soil_value,
        "sound_state": node.sound_state,
        "movement_score": node.movement_score,
        "accel_x": node.accel_x,
        "accel_y": node.accel_y,
        "accel_z": node.accel_z,
        "wifi_rssi": node.wifi_rssi,
        "mpu_ready": node.mpu_ready,
        "is_online": node.is_online,
        "last_seen_at": node.last_seen_at.strftime("%Y-%m-%d %H:%M:%S") if node.last_seen_at else None,
        "updated_at": node.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
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
        "sensor_nodes": [serialize_sensor_node(node) for node in RangerEyeSensorNode.objects.all()[:20]],
    })


@csrf_exempt
@require_POST
def sensor_telemetry(request):
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Invalid JSON payload."}, status=400)

    device_id = str(payload.get("device_id") or "SENSOR-NODE-01").strip()
    if not device_id:
        return JsonResponse({"detail": "device_id is required."}, status=400)

    node, _created = RangerEyeSensorNode.objects.get_or_create(device_id=device_id)
    node.device_name = payload.get("device_name") or node.device_name
    node.location = payload.get("location") or node.location
    node.ip_address = payload.get("ip_address") or request.META.get("REMOTE_ADDR", "")
    node.firmware_version = payload.get("firmware_version") or node.firmware_version
    node.soil_value = payload.get("soil_value")
    node.sound_state = payload.get("sound_state")
    node.movement_score = payload.get("movement_score")
    node.accel_x = payload.get("accel_x")
    node.accel_y = payload.get("accel_y")
    node.accel_z = payload.get("accel_z")
    node.wifi_rssi = payload.get("wifi_rssi")
    node.mpu_ready = bool(payload.get("mpu_ready", False))
    node.raw_payload = payload
    node.last_seen_at = timezone.now()
    node.save()

    return JsonResponse({
        "detail": "Sensor telemetry received.",
        "sensor_node": serialize_sensor_node(node),
    }, status=200)


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
    payload = {}
    content_type = request.META.get("CONTENT_TYPE", "")
    if "application/json" in content_type:
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            payload = {}

    alert_type = payload.get("type") or request.GET.get("type", "sensor")
    location = payload.get("location") or request.GET.get("location", "Protected Plant Zone")
    message = payload.get("message") or (request.body.decode("utf-8") if request.body and not payload else "")
    reported_device_id = payload.get("device_id")

    if alert_type == "plant_disturbance":
        event_type = "Possible Plant Disturbance Detected"
        device_id = reported_device_id or "PLANT-SENSOR-01"
    elif alert_type == "sound_disturbance":
        event_type = "Abnormal Sound Near Protected Plant"
        device_id = reported_device_id or "SOUND-SENSOR-01"
    elif alert_type == "node_disturbance":
        event_type = "Sensor Node Disturbance Alert"
        device_id = reported_device_id or "MPU6050-TILT-01"
    elif alert_type == "theft_alert":
        event_type = "Sensor Node Theft / Shake Alert"
        device_id = reported_device_id or "MPU6050-SHAKE-01"
    elif alert_type == "restricted_zone":
        event_type = "Restricted Zone Activity Detected"
        device_id = reported_device_id or "ZONE-SENSOR-01"
    else:
        event_type = "Sensor Alert"
        device_id = reported_device_id or "SENSOR-NODE-01"

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
