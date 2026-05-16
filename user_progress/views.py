from rest_framework import permissions, viewsets
from django.db.models import Count, Prefetch

from courses.models import Chapter, ChapterProgress, CourseEnrollment, ModuleProgress
from .models import Badge, UserBadge
from .serializers import BadgeStatusSerializer, UserBadgeSerializer
from .services import ensure_badge_rows_for_user, sync_user_badges


def get_request_language(request):
    raw_language = (request.query_params.get('lang') or '').lower()
    if raw_language.startswith('zh'):
        return 'zh'
    if raw_language.startswith('ms'):
        return 'ms'
    return 'en'


class BadgeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BadgeStatusSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Badge.objects.filter(is_active=True).select_related('course')
        if self.request.query_params.get('compact') == '1':
            return queryset
        return queryset.prefetch_related(
            Prefetch('course__chapters', queryset=Chapter.objects.order_by('order').prefetch_related('lessons')),
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        user = self.request.user
        ensure_badge_rows_for_user(user)
        if self.request.query_params.get('sync') == '1':
            sync_user_badges(user, send_notifications=False)
        badges = list(self.get_queryset())
        compact = self.request.query_params.get('compact') == '1'

        user_badges = UserBadge.objects.filter(
            user=user,
            badge_id__in=[badge.id for badge in badges],
        )
        user_badge_map = {row.badge_id: row for row in user_badges}

        granted_regular_badges = user.badge_progress.filter(
            status=UserBadge.STATUS_GRANTED,
            is_awarded=True,
            badge__is_major_badge=False,
        ).count()

        completed_course_ids = set(
            CourseEnrollment.objects.filter(
                user=user,
                status='completed',
            ).values_list('course_id', flat=True)
        )
        module_counts_by_course = {
            row['module__course_id']: row['completed_modules']
            for row in ModuleProgress.objects.filter(
                user=user,
                completed=True,
            ).values('module__course_id').annotate(completed_modules=Count('id'))
        }
        chapter_counts_by_course = {
            row['chapter__course_id']: row['completed_chapters']
            for row in ChapterProgress.objects.filter(
                user=user,
                is_complete=True,
            ).values('chapter__course_id').annotate(completed_chapters=Count('id'))
        }
        all_completed_modules = sum(module_counts_by_course.values())
        all_completed_chapters = sum(chapter_counts_by_course.values())
        all_completed_units = max(all_completed_modules, all_completed_chapters)

        completed_count_map = {}
        completed_badge_count_map = {}
        for badge in badges:
            if badge.is_major_badge:
                completed_count_map[badge.id] = 0
                completed_badge_count_map[badge.id] = granted_regular_badges
                continue
            if badge.course_id in completed_course_ids:
                completed_count = badge.required_completed_modules
            elif badge.course_id:
                completed_count = max(
                    module_counts_by_course.get(badge.course_id, 0),
                    chapter_counts_by_course.get(badge.course_id, 0),
                )
            else:
                completed_count = all_completed_units
            completed_count_map[badge.id] = completed_count
            completed_badge_count_map[badge.id] = 0

        context['user_badge_map'] = user_badge_map
        context['completed_count_map'] = completed_count_map
        context['completed_badge_count_map'] = completed_badge_count_map
        context['compact'] = compact
        context['language'] = get_request_language(self.request)
        return context


class MyBadgeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserBadgeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        ensure_badge_rows_for_user(self.request.user)
        if self.request.query_params.get('sync') == '1':
            sync_user_badges(self.request.user, send_notifications=False)
        return UserBadge.objects.filter(
            user=self.request.user,
            status=UserBadge.STATUS_GRANTED,
            is_awarded=True,
        ).select_related('badge', 'badge__course')
