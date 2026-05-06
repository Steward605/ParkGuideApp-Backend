from django.core.management.base import BaseCommand

from ranger_eye.recorder import run_recording_loop


class Command(BaseCommand):
    help = "Run RangerEye ESP32-CAM automatic video recorder."

    def handle(self, *args, **options):
        run_recording_loop()