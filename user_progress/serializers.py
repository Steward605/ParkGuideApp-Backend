from rest_framework import serializers

from .models import Badge, UserBadge
from .services import (
    build_firebase_media_url,
    get_badge_image_access_url,
    get_badge_storage_path,
    get_localized_value,
)


class BadgeStatusSerializer(serializers.ModelSerializer):
    badge_image_url = serializers.SerializerMethodField()
    localized_name = serializers.SerializerMethodField()
    localized_description = serializers.SerializerMethodField()
    course_id = serializers.SerializerMethodField()  # ✅ Fixed: handles null course
    course_title = serializers.SerializerMethodField()
    course_title_translations = serializers.SerializerMethodField()
    localized_course_title = serializers.SerializerMethodField()
    localized_skills_awarded = serializers.SerializerMethodField()
    localized_lesson_highlights = serializers.SerializerMethodField()
    skills_awarded_translations = serializers.SerializerMethodField()
    lesson_highlights_translations = serializers.SerializerMethodField()
    earned = serializers.SerializerMethodField()
    pending = serializers.SerializerMethodField()
    rejected = serializers.SerializerMethodField()
    in_progress = serializers.SerializerMethodField()
    eligible = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    user_badge_id = serializers.SerializerMethodField()
    is_awarded = serializers.SerializerMethodField()
    awarded_at = serializers.SerializerMethodField()
    revoked_at = serializers.SerializerMethodField()
    completed_modules = serializers.SerializerMethodField()
    completed_badges = serializers.SerializerMethodField()
    progress_current = serializers.SerializerMethodField()
    progress_required = serializers.SerializerMethodField()
    progress_kind = serializers.SerializerMethodField()

    class Meta:
        model = Badge
        fields = [
            'id',
            'name',
            'description',
            'name_translations',
            'description_translations',
            'localized_name',
            'localized_description',
            'badge_image_url',
            'badge_image_source',
            'skills_awarded',
            'skills_awarded_translations',
            'localized_skills_awarded',
            'lesson_highlights',
            'lesson_highlights_translations',
            'localized_lesson_highlights',
            'course_id',
            'course_title',
            'course_title_translations',
            'localized_course_title',
            'required_completed_modules',
            'is_major_badge',
            'required_badges_count',
            'status',
            'user_badge_id',
            'is_awarded',
            'awarded_at',
            'revoked_at',
            'earned',
            'pending',
            'rejected',
            'in_progress',
            'eligible',
            'completed_modules',
            'completed_badges',
            'progress_current',
            'progress_required',
            'progress_kind',
        ]

    def get_fields(self):
        fields = super().get_fields()
        if self.context.get('compact'):
            fields.pop('name_translations', None)
            fields.pop('description_translations', None)
            fields.pop('skills_awarded', None)
            fields.pop('skills_awarded_translations', None)
            fields.pop('lesson_highlights', None)
            fields.pop('lesson_highlights_translations', None)
            fields.pop('course_title_translations', None)
        return fields

    def get_course_title(self, obj):
        if not obj.course:
            return None
        return obj.course.title.get('en', 'Course')

    def get_course_title_translations(self, obj):
        if not obj.course:
            return {}
        return obj.course.title or {}

    def get_language(self):
        return self.context.get('language', 'en')

    def get_localized_name(self, obj):
        return get_localized_value(obj.name_translations, self.get_language(), obj.name)

    def get_localized_description(self, obj):
        return get_localized_value(obj.description_translations, self.get_language(), obj.description)

    def get_localized_course_title(self, obj):
        if not obj.course:
            return None
        return get_localized_value(obj.course.title, self.get_language(), 'Course')

    def get_localized_skills_awarded(self, obj):
        language = self.get_language()
        return [
            get_localized_value(item, language)
            for item in (obj.skills_awarded or [])
            if get_localized_value(item, language)
        ]

    def get_localized_lesson_highlights(self, obj):
        language = self.get_language()
        return [
            get_localized_value(item, language)
            for item in (obj.lesson_highlights or [])
            if get_localized_value(item, language)
        ]

    def get_skills_awarded_translations(self, obj):
        if not obj.course:
            return []
        return [chapter.title or {} for chapter in obj.course.chapters.order_by('order')]

    def get_lesson_highlights_translations(self, obj):
        if not obj.course:
            return []
        return [
            lesson.title or {}
            for chapter in obj.course.chapters.order_by('order').prefetch_related('lessons')
            for lesson in chapter.lessons.all().order_by('order')
        ][:8]

    def get_badge_image_url(self, obj):
        if self.context.get('compact'):
            storage_path = get_badge_storage_path(obj.badge_image_url)
            if storage_path:
                return build_firebase_media_url(storage_path) or obj.badge_image_url
            return obj.badge_image_url
        return get_badge_image_access_url(obj.badge_image_url)

    def get_course_id(self, obj):  # ✅ Added: safely handles null course
        if not obj.course:
            return None
        return obj.course.id

    def get_earned(self, obj):
        status = self.get_status(obj)
        return status == UserBadge.STATUS_GRANTED

    def get_pending(self, obj):
        status = self.get_status(obj)
        return status == UserBadge.STATUS_PENDING

    def get_rejected(self, obj):
        status = self.get_status(obj)
        return status == UserBadge.STATUS_REJECTED

    def get_in_progress(self, obj):
        status = self.get_status(obj)
        return status == UserBadge.STATUS_IN_PROGRESS

    def get_status(self, obj):
        user_badge = self._get_user_badge(obj)
        return user_badge.status if user_badge else UserBadge.STATUS_IN_PROGRESS

    def _get_user_badge(self, obj):
        user_badge_map = self.context.get('user_badge_map', {})
        return user_badge_map.get(obj.id)

    def get_user_badge_id(self, obj):
        user_badge = self._get_user_badge(obj)
        return user_badge.id if user_badge else None

    def get_is_awarded(self, obj):
        user_badge = self._get_user_badge(obj)
        return bool(user_badge and user_badge.is_awarded)

    def get_awarded_at(self, obj):
        user_badge = self._get_user_badge(obj)
        return user_badge.awarded_at if user_badge else None

    def get_revoked_at(self, obj):
        user_badge = self._get_user_badge(obj)
        return user_badge.revoked_at if user_badge else None

    def get_completed_modules(self, obj):
        completed_count_map = self.context.get('completed_count_map', {})
        return completed_count_map.get(obj.id, 0)

    def get_completed_badges(self, obj):
        completed_badge_count_map = self.context.get('completed_badge_count_map', {})
        return completed_badge_count_map.get(obj.id, 0)

    def get_eligible(self, obj):
        if obj.is_major_badge:
            return self.get_completed_badges(obj) >= obj.required_badges_count
        return self.get_completed_modules(obj) >= obj.required_completed_modules

    def get_progress_current(self, obj):
        if obj.is_major_badge:
            return self.get_completed_badges(obj)
        return self.get_completed_modules(obj)

    def get_progress_required(self, obj):
        if obj.is_major_badge:
            return obj.required_badges_count
        return obj.required_completed_modules

    def get_progress_kind(self, obj):
        return 'badges' if obj.is_major_badge else 'modules'


class UserBadgeSerializer(serializers.ModelSerializer):
    badge_name = serializers.CharField(source='badge.name', read_only=True)
    badge_description = serializers.CharField(source='badge.description', read_only=True)
    badge_name_translations = serializers.JSONField(source='badge.name_translations', read_only=True)
    badge_description_translations = serializers.JSONField(source='badge.description_translations', read_only=True)
    badge_image_url = serializers.SerializerMethodField()
    badge_image_source = serializers.CharField(source='badge.badge_image_source', read_only=True)
    badge_skills_awarded = serializers.JSONField(source='badge.skills_awarded', read_only=True)
    badge_skills_awarded_translations = serializers.SerializerMethodField()
    badge_lesson_highlights = serializers.JSONField(source='badge.lesson_highlights', read_only=True)
    badge_lesson_highlights_translations = serializers.SerializerMethodField()
    badge_required_completed_modules = serializers.IntegerField(source='badge.required_completed_modules', read_only=True)
    badge_required_badges_count = serializers.IntegerField(source='badge.required_badges_count', read_only=True)
    badge_is_major_badge = serializers.BooleanField(source='badge.is_major_badge', read_only=True)
    badge_course_id = serializers.SerializerMethodField()  # ✅ Fixed: handles null course
    badge_course_title = serializers.SerializerMethodField()
    badge_course_title_translations = serializers.SerializerMethodField()

    class Meta:
        model = UserBadge
        fields = [
            'id',
            'badge',
            'badge_name',
            'badge_description',
            'badge_name_translations',
            'badge_description_translations',
            'badge_image_url',
            'badge_image_source',
            'badge_skills_awarded',
            'badge_skills_awarded_translations',
            'badge_lesson_highlights',
            'badge_lesson_highlights_translations',
            'badge_required_completed_modules',
            'badge_required_badges_count',
            'badge_is_major_badge',
            'badge_course_id',
            'badge_course_title',
            'badge_course_title_translations',
            'status',
            'is_awarded',
            'awarded_at',
            'revoked_at',
        ]

    def get_badge_course_id(self, obj):  # ✅ Added: safely handles null course
        if not obj.badge.course:
            return None
        return obj.badge.course.id

    def get_badge_image_url(self, obj):
        return get_badge_image_access_url(obj.badge.badge_image_url)

    def get_badge_course_title(self, obj):
        if not obj.badge.course:
            return None
        return obj.badge.course.title.get('en', 'Course')

    def get_badge_course_title_translations(self, obj):
        if not obj.badge.course:
            return {}
        return obj.badge.course.title or {}

    def get_badge_skills_awarded_translations(self, obj):
        if not obj.badge.course:
            return []
        return [chapter.title or {} for chapter in obj.badge.course.chapters.order_by('order')]

    def get_badge_lesson_highlights_translations(self, obj):
        if not obj.badge.course:
            return []
        return [
            lesson.title or {}
            for chapter in obj.badge.course.chapters.order_by('order').prefetch_related('lessons')
            for lesson in chapter.lessons.all().order_by('order')
        ][:8]
