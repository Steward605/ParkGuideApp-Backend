"""
Compatibility wrapper for the previous enhanced AR seed command.
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create comprehensive AR training simulations"

    def handle(self, *args, **options):
        call_command("create_ar_training_data")
