from django.db import models
from django.utils import timezone


class RangerEyeAlert(models.Model):
    STATUS_PENDING = "pending"
    STATUS_REVIEWED = "reviewed"
    STATUS_DISMISSED = "dismissed"

    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending Review"),
        (STATUS_REVIEWED, "Reviewed"),
        (STATUS_DISMISSED, "Dismissed"),
    )

    alert_id = models.CharField(max_length=30, unique=True, db_index=True)
    event_type = models.CharField(max_length=255)
    source = models.CharField(max_length=120, blank=True, default="")
    device_id = models.CharField(max_length=120, blank=True, default="")
    location = models.CharField(max_length=255, blank=True, default="")
    message = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)

    evidence_image = models.ImageField(upload_to="ranger_eye/uploads/", blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.alert_id} - {self.event_type}"


class RangerEyeRecording(models.Model):
    filename = models.CharField(max_length=255)
    video_file = models.FileField(upload_to="ranger_eye/recordings/")
    duration_seconds = models.PositiveIntegerField(default=60)
    source = models.CharField(max_length=120, blank=True, default="ESP32-CAM stream")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.filename


class RangerEyeRecorderStatus(models.Model):
    running = models.BooleanField(default=False)
    last_recording = models.CharField(max_length=255, blank=True, default="None yet")
    next_recording = models.CharField(max_length=255, blank=True, default="Starting soon")
    message = models.TextField(blank=True, default="Video recorder starting...")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "RangerEye Recorder Status"
        verbose_name_plural = "RangerEye Recorder Status"

    def __str__(self):
        return "Recording" if self.running else "Waiting"


class RangerEyeSensorNode(models.Model):
    device_id = models.CharField(max_length=120, unique=True, db_index=True)
    device_name = models.CharField(max_length=120, blank=True, default="ESP32 Sensor Node")
    location = models.CharField(max_length=255, blank=True, default="Protected Plant Zone")
    ip_address = models.CharField(max_length=64, blank=True, default="")
    firmware_version = models.CharField(max_length=40, blank=True, default="")
    soil_value = models.IntegerField(null=True, blank=True)
    sound_state = models.IntegerField(null=True, blank=True)
    movement_score = models.FloatField(null=True, blank=True)
    accel_x = models.FloatField(null=True, blank=True)
    accel_y = models.FloatField(null=True, blank=True)
    accel_z = models.FloatField(null=True, blank=True)
    wifi_rssi = models.IntegerField(null=True, blank=True)
    mpu_ready = models.BooleanField(default=False)
    raw_payload = models.JSONField(default=dict, blank=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-last_seen_at", "-updated_at")

    @property
    def is_online(self):
        if not self.last_seen_at:
            return False
        return (timezone.now() - self.last_seen_at).total_seconds() <= 90

    def __str__(self):
        return f"{self.device_id} - {self.location}"
