from django.db import models


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