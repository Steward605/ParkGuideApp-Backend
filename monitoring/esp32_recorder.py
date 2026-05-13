import subprocess
import tempfile
import time
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import requests
from django.core.exceptions import ImproperlyConfigured

try:
    import cv2
except Exception:  # pragma: no cover - optional dependency during local setup
    cv2 = None

try:
    import imageio_ffmpeg
except Exception:  # pragma: no cover - optional dependency during local setup
    imageio_ffmpeg = None

try:
    import numpy as np
except Exception:  # pragma: no cover - optional dependency during local setup
    np = None


DEFAULT_CAPTURE_FPS = 6
DEFAULT_DURATION_SECONDS = 15
DEFAULT_WIDTH = 320
DEFAULT_HEIGHT = 240
MIN_REAL_FRAMES = 2
MIN_VIDEO_SIZE_BYTES = 4000


def normalize_base_url(value):
    base = str(value or "").strip().rstrip("/")
    if not base:
        raise ValueError("ESP32 base URL is required.")
    if not base.startswith(("http://", "https://")):
        base = f"http://{base}"
    return base


def build_capture_url(*, base_url="", capture_url=""):
    if capture_url:
        return str(capture_url).strip()
    return f"{normalize_base_url(base_url)}/capture"


def build_status_url(*, base_url=""):
    return f"{normalize_base_url(base_url)}/status"


def build_stream_url(*, base_url="", stream_url=""):
    if stream_url:
        return str(stream_url).strip()

    parsed = urlparse(normalize_base_url(base_url))
    hostname = parsed.hostname or parsed.netloc
    if not hostname:
        raise ValueError("Invalid ESP32 base URL.")

    netloc = f"{hostname}:81"
    return urlunparse((parsed.scheme or "http", netloc, "/stream", "", "", ""))


def fetch_status(base_url, *, timeout=8):
    response = requests.get(build_status_url(base_url=base_url), timeout=(2, timeout))
    response.raise_for_status()
    return response.json()


def _encode_frames_to_mp4(frame_paths, output_path, *, fps=DEFAULT_CAPTURE_FPS, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
    if imageio_ffmpeg is None:
        raise ImproperlyConfigured("imageio-ffmpeg is required to encode ESP32 footage.")

    frame_dir = frame_paths[0].parent
    command = [
        imageio_ffmpeg.get_ffmpeg_exe(),
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-framerate",
        str(fps),
        "-i",
        str(frame_dir / "frame_%04d.jpg"),
        "-vf",
        f"scale={width}:{height}",
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(output_path),
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=90)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or "FFmpeg could not encode ESP32 captures.")


def encode_jpeg_bytes_to_mp4(jpeg_items, *, fps=DEFAULT_CAPTURE_FPS, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
    if cv2 is None or np is None:
        raise ImproperlyConfigured("OpenCV and NumPy are required to encode ESP32-CAM footage.")

    temp_dir = Path(tempfile.mkdtemp(prefix="parkguide_uploaded_esp32_frames_"))
    output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    output_path = Path(output_file.name)
    output_file.close()

    frame_paths = []
    decode_errors = 0

    try:
        for item in jpeg_items:
            content = item.read() if hasattr(item, "read") else item
            frame = _decode_jpeg(content, width=width, height=height)
            if frame is None:
                decode_errors += 1
                continue

            frame_path = temp_dir / f"frame_{len(frame_paths) + 1:04d}.jpg"
            cv2.imwrite(str(frame_path), frame)
            frame_paths.append(frame_path)

        if len(frame_paths) < MIN_REAL_FRAMES:
            raise RuntimeError(f"Only {len(frame_paths)} uploaded ESP32 frame(s) could be decoded.")

        _encode_frames_to_mp4(frame_paths, output_path, fps=fps, width=width, height=height)
        if not output_path.exists() or output_path.stat().st_size < MIN_VIDEO_SIZE_BYTES:
            raise RuntimeError("Uploaded ESP32 frames did not produce a valid video clip.")

        return {
            "path": output_path,
            "duration_seconds": max(1, round(len(frame_paths) / fps)),
            "fps": fps,
            "target_frames": len(jpeg_items),
            "saved_frames": len(frame_paths),
            "real_frames": len(frame_paths),
            "errors": [f"{decode_errors} frame(s) failed JPEG decode."] if decode_errors else [],
        }
    except Exception:
        try:
            output_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    finally:
        for frame_path in frame_paths:
            try:
                frame_path.unlink(missing_ok=True)
            except OSError:
                pass
        try:
            temp_dir.rmdir()
        except OSError:
            pass


def encode_uploaded_jpegs_to_mp4(uploaded_frames, *, fps=DEFAULT_CAPTURE_FPS, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
    return encode_jpeg_bytes_to_mp4(uploaded_frames, fps=fps, width=width, height=height)


def _decode_jpeg(content, *, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
    if cv2 is None or np is None:
        raise ImproperlyConfigured("OpenCV and NumPy are required to record ESP32-CAM footage.")
    if not content:
        return None
    array = np.frombuffer(content, dtype=np.uint8)
    frame = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if frame is None:
        return None
    return cv2.resize(frame, (width, height))


def record_capture_clip(
    *,
    base_url="",
    capture_url="",
    duration_seconds=DEFAULT_DURATION_SECONDS,
    fps=DEFAULT_CAPTURE_FPS,
    width=DEFAULT_WIDTH,
    height=DEFAULT_HEIGHT,
):
    if cv2 is None or np is None:
        raise ImproperlyConfigured("OpenCV and NumPy are required to record ESP32-CAM footage.")

    capture_url = build_capture_url(base_url=base_url, capture_url=capture_url)
    duration_seconds = max(3, min(int(duration_seconds or DEFAULT_DURATION_SECONDS), 20))
    fps = max(1, min(int(fps or DEFAULT_CAPTURE_FPS), 3))
    target_frames = max(MIN_REAL_FRAMES, duration_seconds * fps)
    interval = 1.0 / fps
    deadline = time.monotonic() + duration_seconds + 8

    temp_dir = Path(tempfile.mkdtemp(prefix="parkguide_esp32_frames_"))
    output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    output_path = Path(output_file.name)
    output_file.close()

    frame_paths = []
    errors = []
    real_frames = 0
    last_frame = None

    try:
        with requests.Session() as session:
            for frame_number in range(1, target_frames + 1):
                if time.monotonic() > deadline:
                    errors.append("Capture deadline reached before target frame count.")
                    break

                loop_start = time.monotonic()
                frame = None
                try:
                    response = session.get(capture_url, timeout=(2, 6))
                    response.raise_for_status()
                    frame = _decode_jpeg(response.content, width=width, height=height)
                    if frame is not None:
                        last_frame = frame
                        real_frames += 1
                    else:
                        errors.append(f"Frame {frame_number}: JPEG decode failed.")
                except requests.RequestException as exc:
                    errors.append(f"Frame {frame_number}: {exc}")

                if frame is None and last_frame is not None:
                    frame = last_frame.copy()
                if frame is None:
                    continue

                frame_path = temp_dir / f"frame_{len(frame_paths) + 1:04d}.jpg"
                cv2.imwrite(str(frame_path), frame)
                frame_paths.append(frame_path)

                sleep_for = interval - (time.monotonic() - loop_start)
                if sleep_for > 0:
                    time.sleep(sleep_for)

        if real_frames < MIN_REAL_FRAMES:
            raise RuntimeError(
                f"Only {real_frames} real ESP32 frame(s) captured from {capture_url}. "
                f"Last errors: {' | '.join(errors[-3:]) if errors else 'none'}"
            )

        _encode_frames_to_mp4(frame_paths, output_path, fps=fps, width=width, height=height)
        if not output_path.exists() or output_path.stat().st_size < MIN_VIDEO_SIZE_BYTES:
            raise RuntimeError("ESP32 clip was not created or was too small.")

        return {
            "path": output_path,
            "capture_url": capture_url,
            "duration_seconds": duration_seconds,
            "fps": fps,
            "target_frames": target_frames,
            "saved_frames": len(frame_paths),
            "real_frames": real_frames,
            "errors": errors[-5:],
        }
    except Exception:
        try:
            output_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    finally:
        for frame_path in frame_paths:
            try:
                frame_path.unlink(missing_ok=True)
            except OSError:
                pass
        try:
            temp_dir.rmdir()
        except OSError:
            pass


def record_esp32_stream_to_mp4(
    *,
    base_url="",
    stream_url="",
    duration_seconds=DEFAULT_DURATION_SECONDS,
    fps=DEFAULT_CAPTURE_FPS,
    width=DEFAULT_WIDTH,
    height=DEFAULT_HEIGHT,
):
    """
    Record from MJPEG stream directly using OpenCV VideoCapture.
    More reliable than individual /capture endpoint calls.
    """
    if cv2 is None or np is None:
        raise ImproperlyConfigured("OpenCV and NumPy are required to record ESP32-CAM footage.")

    stream_url = build_stream_url(base_url=base_url, stream_url=stream_url)
    duration_seconds = max(3, min(int(duration_seconds or DEFAULT_DURATION_SECONDS), 20))
    fps = max(1, min(int(fps or DEFAULT_CAPTURE_FPS), 6))
    target_frames = max(MIN_REAL_FRAMES, duration_seconds * fps)

    output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    output_path = Path(output_file.name)
    output_file.close()

    frame_paths = []
    errors = []
    real_frames = 0

    try:
        # Open MJPEG stream with OpenCV
        capture = cv2.VideoCapture(stream_url)
        if not capture.isOpened():
            raise RuntimeError(f"Could not open MJPEG stream: {stream_url}")

        deadline = time.monotonic() + duration_seconds + 5
        frame_number = 0

        try:
            while time.monotonic() < deadline and frame_number < target_frames:
                ret, frame = capture.read()
                if not ret:
                    errors.append(f"Frame {frame_number + 1}: Failed to read from stream.")
                    if frame_number >= MIN_REAL_FRAMES:
                        break
                    continue

                # Resize frame to target dimensions
                frame = cv2.resize(frame, (width, height))

                frame_path = Path(tempfile.gettempdir()) / f"esp32_stream_frame_{frame_number + 1:04d}.jpg"
                if cv2.imwrite(str(frame_path), frame):
                    frame_paths.append(frame_path)
                    real_frames += 1
                else:
                    errors.append(f"Frame {frame_number + 1}: Failed to save JPEG.")

                frame_number += 1

                # Throttle frame extraction if necessary
                if fps > 0:
                    delay = int(1000 / fps)  # milliseconds
                    capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffering
        finally:
            capture.release()

        if real_frames < MIN_REAL_FRAMES:
            raise RuntimeError(
                f"Only {real_frames} real ESP32 frame(s) captured from stream. "
                f"Last errors: {' | '.join(errors[-3:]) if errors else 'none'}"
            )

        temp_dir = Path(tempfile.mkdtemp(prefix="parkguide_esp32_stream_"))
        try:
            # Move frames to temp directory for encoding
            for i, old_path in enumerate(frame_paths, 1):
                new_path = temp_dir / f"frame_{i:04d}.jpg"
                old_path.rename(new_path)
                frame_paths[i - 1] = new_path

            _encode_frames_to_mp4(frame_paths, output_path, fps=fps, width=width, height=height)
            if not output_path.exists() or output_path.stat().st_size < MIN_VIDEO_SIZE_BYTES:
                raise RuntimeError("ESP32 stream clip was not created or was too small.")

            return {
                "path": output_path,
                "stream_url": stream_url,
                "duration_seconds": duration_seconds,
                "fps": fps,
                "target_frames": target_frames,
                "saved_frames": len(frame_paths),
                "real_frames": real_frames,
                "errors": errors[-5:],
            }
        finally:
            for frame_path in frame_paths:
                try:
                    frame_path.unlink(missing_ok=True)
                except OSError:
                    pass
            try:
                temp_dir.rmdir()
            except OSError:
                pass
    except Exception:
        try:
            output_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise
