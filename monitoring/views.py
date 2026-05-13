import tempfile
import time
import uuid
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from rest_framework import permissions, status, viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from secure_files.services.firebase_storage import delete_file as delete_firebase_blob, download_file_bytes, generate_upload_url

from .esp32_recorder import build_capture_url, build_stream_url, encode_jpeg_bytes_to_mp4, encode_uploaded_jpegs_to_mp4, fetch_status, record_capture_clip, record_esp32_stream_to_mp4
from .models import MonitorClip, MonitorSession, ViolationAlert
from .serializers import MonitorClipSerializer, MonitorSessionSerializer, ViolationAlertSerializer
from .services import process_monitoring_clip, stop_active_session, upsert_active_session


class MonitorStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        session = MonitorSession.objects.filter(user=request.user).order_by("-updated_at").first()
        alert_qs = ViolationAlert.objects.all()
        latest_alert = alert_qs.order_by("-received_at").first()

        is_live = bool(session and session.is_active)
        state = "live" if is_live else "offline"
        if session and not session.is_active:
            state = "offline"
        elif session and session.last_seen_at is None:
            state = "checking"

        return Response(
            {
                "is_live": is_live,
                "state": state,
                "source": MonitorSession.SOURCE_ESP32,
                "camera_source": session.camera_source if session else "RE-CAM-01",
                "stream_url": None,
                "session_id": session.id if session else None,
                "alert_count": alert_qs.count(),
                "last_seen_at": session.last_seen_at if session else (latest_alert.received_at if latest_alert else None),
                "message": "Camera module is live." if is_live else "Camera module is not connected.",
                "clip_interval_minutes": session.clip_interval_minutes if session else 5,
            }
        )


class MonitorSessionStartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        source_mode = MonitorSession.SOURCE_ESP32
        camera_source = request.data.get("camera_source", "RE-CAM-01")
        clip_interval_minutes = request.data.get("clip_interval_minutes", 5)

        session = upsert_active_session(
            request.user,
            source_mode=source_mode,
            camera_source=camera_source,
            clip_interval_minutes=clip_interval_minutes,
        )
        session.alert_count = ViolationAlert.objects.count()
        session.last_alert_at = ViolationAlert.objects.order_by("-received_at").values_list("received_at", flat=True).first()
        serializer = MonitorSessionSerializer(session)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MonitorEsp32RecordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        base_url = str(request.data.get("base_url", "")).strip()
        capture_url = str(request.data.get("capture_url", "")).strip()
        stream_url = str(request.data.get("stream_url", "")).strip()
        duration_seconds = request.data.get("duration_seconds", 8)
        fps = request.data.get("fps", 6)
        camera_source = request.data.get("camera_source") or base_url or capture_url or "RE-CAM-01"
        guide_name = request.data.get("guide_name", request.user.get_full_name() or request.user.get_username())
        location = request.data.get("location", "ESP32-CAM monitoring")
        clip_interval_minutes = request.data.get("clip_interval_minutes", 5)

        recording = None
        try:
            if base_url:
                try:
                    device_status = fetch_status(base_url)
                    capture_url = capture_url or device_status.get("captureUrl", "")
                    stream_url = stream_url or device_status.get("streamUrl", "")
                except Exception:
                    device_status = None
            else:
                device_status = None

            capture_url = build_capture_url(base_url=base_url, capture_url=capture_url)
            if base_url and not stream_url:
                stream_url = build_stream_url(base_url=base_url)

            session = upsert_active_session(
                request.user,
                source_mode=MonitorSession.SOURCE_ESP32,
                camera_source=camera_source,
                clip_interval_minutes=clip_interval_minutes,
            )

            # Try MJPEG stream first (more reliable), fall back to individual captures
            recording = None
            recording_mode = "snapshot_fallback"
            stream_error = None
            
            if stream_url:
                try:
                    recording = record_esp32_stream_to_mp4(
                        stream_url=stream_url,
                        duration_seconds=duration_seconds,
                        fps=fps,
                    )
                    recording_mode = "mjpeg_stream"
                except Exception as stream_exc:
                    stream_error = str(stream_exc)
                    recording = None
            
            if recording is None:
                # Fall back to individual captures
                recording = record_capture_clip(
                    base_url=base_url,
                    capture_url=capture_url,
                    duration_seconds=duration_seconds,
                    fps=fps,
                )
                if stream_error:
                    recording["errors"].insert(0, f"Stream failed, fell back to snapshots: {stream_error}")
            
            recorded_path = recording["path"]
            result = process_monitoring_clip(
                recorded_path,
                owner=request.user,
                uploaded_name=f"esp32-monitor-{session.id}-{recorded_path.name}",
                content_type="video/mp4",
                camera_source=camera_source,
                source_mode=MonitorSession.SOURCE_ESP32,
                guide_name=guide_name,
                location=location,
                clip_duration=f'{recording["duration_seconds"]}s',
                clip_interval_minutes=clip_interval_minutes,
                annotate=True,
                send_notifications=True,
                created_by=request.user if request.user.is_staff else None,
                keep_without_detection=True,
            )

            recording_payload = {
                "mode": recording_mode,
                "base_url": base_url,
                "capture_url": capture_url,
                "stream_url": stream_url,
                "duration_seconds": recording["duration_seconds"],
                "fps": recording["fps"],
                "target_frames": recording["target_frames"],
                "saved_frames": recording["saved_frames"],
                "real_frames": recording["real_frames"],
                "warnings": recording["errors"],
                "device": device_status or {},
            }

            if result["alert"] is None:
                clip = MonitorClip.objects.create(
                    user=request.user,
                    session=session,
                    evidence_file=result["secure_file"],
                    source_mode=MonitorSession.SOURCE_ESP32,
                    camera_source=camera_source,
                    location=location,
                    status=MonitorClip.STATUS_NO_DETECTION,
                    video_filename=result["secure_file"].original_name if result["secure_file"] else recorded_path.name,
                    video_duration=f'{recording["duration_seconds"]}s',
                    details="Recorded ESP32-CAM footage. AI did not detect a monitored violation.",
                    raw_payload=recording_payload,
                )
                return Response(
                    {
                        "alert": None,
                        "clip": MonitorClipSerializer(clip).data,
                        "secure_file": result["secure_file"].id if result["secure_file"] else None,
                        "deleted_after_processing": False,
                        "recording": recording_payload,
                        "detail": "ESP32 clip recorded and processed; no violation was detected.",
                    },
                    status=status.HTTP_201_CREATED,
                )

            clip = MonitorClip.objects.create(
                user=request.user,
                session=result["session"],
                evidence_file=result["secure_file"],
                alert=result["alert"],
                source_mode=MonitorSession.SOURCE_ESP32,
                camera_source=camera_source,
                location=location,
                status=MonitorClip.STATUS_ALERT,
                video_filename=result["secure_file"].original_name if result["secure_file"] else recorded_path.name,
                video_duration=f'{recording["duration_seconds"]}s',
                details="Recorded ESP32-CAM footage. AI generated an alert.",
                raw_payload=recording_payload,
            )

            return Response(
                {
                    "alert": ViolationAlertSerializer(result["alert"]).data,
                    "clip": MonitorClipSerializer(clip).data,
                    "secure_file": result["secure_file"].id if result["secure_file"] else None,
                    "deleted_after_processing": False,
                    "recording": recording_payload,
                },
                status=status.HTTP_201_CREATED,
            )
        except (ImproperlyConfigured, RuntimeError, ValueError) as exc:
            return Response(
                {
                    "detail": str(exc),
                    "base_url": base_url,
                    "capture_url": capture_url,
                    "stream_url": stream_url,
                    "hint": "Restart the ESP32-CAM and verify /capture opens from the backend machine.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        finally:
            if recording and recording.get("path"):
                try:
                    Path(recording["path"]).unlink(missing_ok=True)
                except OSError:
                    pass


class MonitorSessionStopView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        session = stop_active_session(request.user)
        if session is None:
            return Response({"localOnly": True, "sessionActive": False}, status=status.HTTP_200_OK)
        session.alert_count = ViolationAlert.objects.count()
        session.last_alert_at = ViolationAlert.objects.order_by("-received_at").values_list("received_at", flat=True).first()
        serializer = MonitorSessionSerializer(session)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MonitorEsp32FramesUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        frames = request.FILES.getlist("frames")
        if not frames:
            return Response({"detail": "Missing frames field."}, status=status.HTTP_400_BAD_REQUEST)

        base_url = str(request.data.get("base_url", "")).strip()
        camera_source = request.data.get("camera_source") or base_url or "RE-CAM-01"
        guide_name = request.data.get("guide_name", request.user.get_full_name() or request.user.get_username())
        location = request.data.get("location", "ESP32-CAM monitoring")
        clip_interval_minutes = request.data.get("clip_interval_minutes", 5)
        fps = request.data.get("fps", 1)

        recording = None
        try:
            session = upsert_active_session(
                request.user,
                source_mode=MonitorSession.SOURCE_ESP32,
                camera_source=camera_source,
                clip_interval_minutes=clip_interval_minutes,
            )
            recording = encode_uploaded_jpegs_to_mp4(frames, fps=fps)
            recorded_path = recording["path"]
            result = process_monitoring_clip(
                recorded_path,
                owner=request.user,
                uploaded_name=f"esp32-relay-{session.id}-{recorded_path.name}",
                content_type="video/mp4",
                camera_source=camera_source,
                source_mode=MonitorSession.SOURCE_ESP32,
                guide_name=guide_name,
                location=location,
                clip_duration=f'{recording["duration_seconds"]}s',
                clip_interval_minutes=clip_interval_minutes,
                annotate=True,
                send_notifications=True,
                created_by=request.user if request.user.is_staff else None,
                keep_without_detection=True,
            )

            recording_payload = {
                "mode": "phone_relay_frames",
                "base_url": base_url,
                "duration_seconds": recording["duration_seconds"],
                "fps": recording["fps"],
                "target_frames": recording["target_frames"],
                "saved_frames": recording["saved_frames"],
                "real_frames": recording["real_frames"],
                "warnings": recording["errors"],
            }

            if result["alert"] is None:
                clip = MonitorClip.objects.create(
                    user=request.user,
                    session=session,
                    evidence_file=result["secure_file"],
                    source_mode=MonitorSession.SOURCE_ESP32,
                    camera_source=camera_source,
                    location=location,
                    status=MonitorClip.STATUS_NO_DETECTION,
                    video_filename=result["secure_file"].original_name if result["secure_file"] else recorded_path.name,
                    video_duration=f'{recording["duration_seconds"]}s',
                    details="Phone relayed ESP32-CAM footage. AI did not detect a monitored violation.",
                    raw_payload=recording_payload,
                )
                return Response(
                    {
                        "alert": None,
                        "clip": MonitorClipSerializer(clip).data,
                        "secure_file": result["secure_file"].id if result["secure_file"] else None,
                        "deleted_after_processing": False,
                        "recording": recording_payload,
                        "detail": "ESP32 footage saved. No violation was detected.",
                    },
                    status=status.HTTP_201_CREATED,
                )

            clip = MonitorClip.objects.create(
                user=request.user,
                session=result["session"],
                evidence_file=result["secure_file"],
                alert=result["alert"],
                source_mode=MonitorSession.SOURCE_ESP32,
                camera_source=camera_source,
                location=location,
                status=MonitorClip.STATUS_ALERT,
                video_filename=result["secure_file"].original_name if result["secure_file"] else recorded_path.name,
                video_duration=f'{recording["duration_seconds"]}s',
                details="Phone relayed ESP32-CAM footage. AI generated an alert.",
                raw_payload=recording_payload,
            )
            return Response(
                {
                    "alert": ViolationAlertSerializer(result["alert"]).data,
                    "clip": MonitorClipSerializer(clip).data,
                    "secure_file": result["secure_file"].id if result["secure_file"] else None,
                    "deleted_after_processing": False,
                    "recording": recording_payload,
                },
                status=status.HTTP_201_CREATED,
            )
        except (ImproperlyConfigured, RuntimeError, ValueError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        finally:
            if recording and recording.get("path"):
                try:
                    Path(recording["path"]).unlink(missing_ok=True)
                except OSError:
                    pass


class MonitorEsp32FrameUploadSessionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            # Allow larger frame upload sessions from phones (capped to prevent abuse)
            # Previously capped at 20 which is too small for longer captures from phones.
            frame_count = max(1, min(int(request.data.get("frame_count", 8)), 120))
        except (TypeError, ValueError):
            frame_count = 8

        session_id = uuid.uuid4().hex
        timestamp = int(time.time())
        uploads = []
        for index in range(frame_count):
            blob_path = f"monitor/raw_frames/{request.user.id}/{timestamp}_{session_id}/frame_{index + 1:03d}.jpg"
            uploads.append(
                {
                    "index": index,
                    "blob_path": blob_path,
                    "upload_url": generate_upload_url(blob_path, content_type="image/jpeg", expires_seconds=900),
                    "content_type": "image/jpeg",
                }
            )

        return Response({"session_id": session_id, "uploads": uploads}, status=status.HTTP_200_OK)


class MonitorEsp32FirebaseFramesProcessView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        blob_paths = request.data.get("blob_paths", [])
        if not isinstance(blob_paths, list) or not blob_paths:
            return Response({"detail": "blob_paths must be a non-empty list."}, status=status.HTTP_400_BAD_REQUEST)

        base_url = str(request.data.get("base_url", "")).strip()
        camera_source = request.data.get("camera_source") or base_url or "RE-CAM-01"
        guide_name = request.data.get("guide_name", request.user.get_full_name() or request.user.get_username())
        location = request.data.get("location", "ESP32-CAM monitoring")
        clip_interval_minutes = request.data.get("clip_interval_minutes", 5)
        fps = request.data.get("fps", 1)
        recording = None

        try:
            jpeg_bytes = []
            for blob_path in blob_paths:
                data, _content_type = download_file_bytes(blob_path)
                jpeg_bytes.append(data)

            session = upsert_active_session(
                request.user,
                source_mode=MonitorSession.SOURCE_ESP32,
                camera_source=camera_source,
                clip_interval_minutes=clip_interval_minutes,
            )
            recording = encode_jpeg_bytes_to_mp4(jpeg_bytes, fps=fps)
            recorded_path = recording["path"]
            result = process_monitoring_clip(
                recorded_path,
                owner=request.user,
                uploaded_name=f"esp32-firebase-{session.id}-{recorded_path.name}",
                content_type="video/mp4",
                camera_source=camera_source,
                source_mode=MonitorSession.SOURCE_ESP32,
                guide_name=guide_name,
                location=location,
                clip_duration=f'{recording["duration_seconds"]}s',
                clip_interval_minutes=clip_interval_minutes,
                annotate=True,
                send_notifications=True,
                created_by=request.user if request.user.is_staff else None,
                keep_without_detection=True,
            )

            recording_payload = {
                "mode": "firebase_frame_upload",
                "base_url": base_url,
                "frame_blob_paths": blob_paths,
                "duration_seconds": recording["duration_seconds"],
                "fps": recording["fps"],
                "target_frames": recording["target_frames"],
                "saved_frames": recording["saved_frames"],
                "real_frames": recording["real_frames"],
                "warnings": recording["errors"],
            }

            if result["alert"] is None:
                clip = MonitorClip.objects.create(
                    user=request.user,
                    session=session,
                    evidence_file=result["secure_file"],
                    source_mode=MonitorSession.SOURCE_ESP32,
                    camera_source=camera_source,
                    location=location,
                    status=MonitorClip.STATUS_NO_DETECTION,
                    video_filename=result["secure_file"].original_name if result["secure_file"] else recorded_path.name,
                    video_duration=f'{recording["duration_seconds"]}s',
                    details="Firebase-uploaded ESP32-CAM footage. AI did not detect a monitored violation.",
                    raw_payload=recording_payload,
                )
                response_payload = {
                    "alert": None,
                    "clip": MonitorClipSerializer(clip).data,
                    "secure_file": result["secure_file"].id if result["secure_file"] else None,
                    "deleted_after_processing": False,
                    "recording": recording_payload,
                    "detail": "ESP32 footage processed from Firebase. No violation was detected.",
                }
            else:
                clip = MonitorClip.objects.create(
                    user=request.user,
                    session=result["session"],
                    evidence_file=result["secure_file"],
                    alert=result["alert"],
                    source_mode=MonitorSession.SOURCE_ESP32,
                    camera_source=camera_source,
                    location=location,
                    status=MonitorClip.STATUS_ALERT,
                    video_filename=result["secure_file"].original_name if result["secure_file"] else recorded_path.name,
                    video_duration=f'{recording["duration_seconds"]}s',
                    details="Firebase-uploaded ESP32-CAM footage. AI generated an alert.",
                    raw_payload=recording_payload,
                )
                response_payload = {
                    "alert": ViolationAlertSerializer(result["alert"]).data,
                    "clip": MonitorClipSerializer(clip).data,
                    "secure_file": result["secure_file"].id if result["secure_file"] else None,
                    "deleted_after_processing": False,
                    "recording": recording_payload,
                }

            for blob_path in blob_paths:
                try:
                    delete_firebase_blob(blob_path)
                except Exception:
                    pass

            return Response(response_payload, status=status.HTTP_201_CREATED)
        except (ImproperlyConfigured, RuntimeError, ValueError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        finally:
            if recording and recording.get("path"):
                try:
                    Path(recording["path"]).unlink(missing_ok=True)
                except OSError:
                    pass


class ViolationAlertViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ViolationAlertSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ViolationAlert.objects.select_related("session", "evidence_file", "user").order_by("-received_at", "-id")


class MonitorClipViewSet(viewsets.ModelViewSet):
    serializer_class = MonitorClipSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "head", "options", "delete"]

    def get_queryset(self):
        qs = MonitorClip.objects.select_related("session", "evidence_file", "alert", "user").order_by("-recorded_at", "-id")
        if self.request.user.is_staff:
            return qs
        return qs.filter(user=self.request.user)

    def perform_destroy(self, instance):
        secure_file = instance.evidence_file
        alert = instance.alert
        if alert and alert.evidence_file_id == getattr(secure_file, "id", None):
            alert.evidence_file = None
            alert.video_filename = ""
            alert.evidence_status = "Evidence footage deleted by guide."
            alert.save(update_fields=["evidence_file", "video_filename", "evidence_status"])

        instance.delete()

        if not secure_file:
            return

        still_used = (
            MonitorClip.objects.filter(evidence_file=secure_file).exists()
            or ViolationAlert.objects.filter(evidence_file=secure_file).exists()
        )
        if still_used:
            return

        try:
            delete_firebase_blob(secure_file.s3_key)
        except Exception:
            pass
        secure_file.delete()


class MonitorEvidenceUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded = request.FILES.get("file")
        if not uploaded:
            return Response({"detail": "Missing file field."}, status=status.HTTP_400_BAD_REQUEST)

        source_mode = MonitorSession.SOURCE_ESP32
        camera_source = request.data.get("camera_source", "RE-CAM-01")
        guide_name = request.data.get("guide_name", request.user.get_full_name() or request.user.get_username())
        location = request.data.get("location", "Field monitoring preview")
        clip_duration = request.data.get("clip_duration", request.data.get("video_duration", ""))
        clip_interval_minutes = request.data.get("clip_interval_minutes", 5)

        temp_path = None
        try:
            suffix = Path(uploaded.name).suffix or ".mp4"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                for chunk in uploaded.chunks():
                    temp_file.write(chunk)
                temp_path = Path(temp_file.name)

            result = process_monitoring_clip(
                temp_path,
                owner=request.user,
                uploaded_name=uploaded.name,
                content_type=getattr(uploaded, "content_type", "") or "",
                camera_source=camera_source,
                source_mode=source_mode,
                guide_name=guide_name,
                location=location,
                clip_duration=clip_duration,
                clip_interval_minutes=clip_interval_minutes,
                annotate=False,
                send_notifications=True,
                created_by=request.user if request.user.is_staff else None,
                keep_without_detection=True,
            )
            if result["alert"] is None:
                clip = MonitorClip.objects.create(
                    user=request.user,
                    session=result["session"],
                    evidence_file=result["secure_file"],
                    source_mode=MonitorSession.SOURCE_ESP32,
                    camera_source=camera_source,
                    location=location,
                    status=MonitorClip.STATUS_NO_DETECTION,
                    video_filename=result["secure_file"].original_name if result["secure_file"] else uploaded.name,
                    video_duration=clip_duration,
                    details="Uploaded monitoring footage. AI did not detect a monitored violation.",
                    raw_payload={"upload_endpoint": "monitor/evidence"},
                )
                return Response(
                    {
                        "clip": MonitorClipSerializer(clip).data,
                        "secure_file": result["secure_file"].id if result["secure_file"] else None,
                        "deleted_after_processing": False,
                        "detail": "No violation was detected. The uploaded clip was saved for review.",
                    },
                    status=status.HTTP_201_CREATED,
                )

            secure_file = result["secure_file"]
            alert = result["alert"]
            clip = MonitorClip.objects.create(
                user=request.user,
                session=result["session"],
                evidence_file=secure_file,
                alert=alert,
                source_mode=MonitorSession.SOURCE_ESP32,
                camera_source=camera_source,
                location=location,
                status=MonitorClip.STATUS_ALERT,
                video_filename=secure_file.original_name if secure_file else uploaded.name,
                video_duration=clip_duration,
                details="Uploaded monitoring footage. AI generated an alert.",
                raw_payload={"upload_endpoint": "monitor/evidence"},
            )
            serializer = ViolationAlertSerializer(alert)
            return Response(
                {
                    "secure_file": secure_file.id,
                    "alert": serializer.data,
                    "clip": MonitorClipSerializer(clip).data,
                },
                status=status.HTTP_201_CREATED,
            )
        except ImproperlyConfigured as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        finally:
            if temp_path and temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
