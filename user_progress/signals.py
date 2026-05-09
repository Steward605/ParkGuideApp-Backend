from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import CustomUser
from courses.models import ModuleProgress

from .models import Badge
from .services import ensure_badge_rows_for_user, sync_user_badges


@receiver(post_save, sender=CustomUser)
def initialize_badges_for_new_user(sender, instance, created, **kwargs):
    if not created:
        return
    ensure_badge_rows_for_user(instance)
    sync_user_badges(instance)


@receiver(post_save, sender=Badge)
def sync_badges_when_badge_changes(sender, instance, created, **kwargs):
    # Badge definition edits can happen in bulk from the dashboard/seed commands.
    # A full all-user eligibility sync here makes those requests feel like they
    # hang forever. UserBadge rows are created lazily when users open badges, and
    # eligibility is synced on course completion/admin sync actions.
    return


@receiver(post_save, sender=ModuleProgress)
def sync_badges_when_module_progress_changes(sender, instance, **kwargs):
    sync_user_badges(instance.user)
