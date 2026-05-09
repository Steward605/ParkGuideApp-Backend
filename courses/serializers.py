# Comprehensive serializers for new registration-based course system

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Course, Chapter, Lesson, PracticeExercise, Quiz,
    CourseEnrollment, ChapterProgress, LessonProgress,
    PracticeAttempt, QuizAttempt,
    Module, ModuleProgress, CourseProgress  # Legacy
)

User = get_user_model()

# ============================================================================
# MULTI-LANGUAGE SUPPORT
# ============================================================================

class MultiLanguageField(serializers.Field):
    """Custom field that converts between JSON {en, ms, zh} and separate language fields"""
    
    def to_representation(self, value):
        """Convert JSON to separate language fields"""
        if value is None:
            return {'en': '', 'ms': '', 'zh': ''}
        return value
    
    def to_internal_value(self, data):
        """Convert separate language fields to JSON"""
        if isinstance(data, dict):
            return data
        raise serializers.ValidationError("Must be an object with language keys (en, ms, zh)")


# ============================================================================
# LESSON & CONTENT SERIALIZERS
# ============================================================================

class LessonSerializer(serializers.ModelSerializer):
    title = MultiLanguageField()
    content_text = MultiLanguageField(required=False, allow_null=True)
    ar_scenario_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'chapter', 'title', 'content_text', 'content_images',
            'content_videos', 'ar_scenario', 'ar_scenario_info', 'order',
            'estimated_time'
        ]

    def get_ar_scenario_info(self, obj):
        scenario = obj.ar_scenario
        if not scenario:
            return None
        return {
            'id': scenario.id,
            'code': scenario.code,
            'title': scenario.title,
            'description': scenario.description,
            'scenario_type': scenario.scenario_type,
            'difficulty': scenario.difficulty,
            'duration_minutes': scenario.duration_minutes,
            'thumbnail': scenario.thumbnail,
            'initial_panorama_url': scenario.initial_panorama_url,
        }


class LessonCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating lessons with multi-language support"""
    chapter = serializers.PrimaryKeyRelatedField(queryset=Chapter.objects.all(), required=True)
    
    title_en = serializers.CharField(required=True, help_text="English title")
    title_ms = serializers.CharField(required=False, allow_blank=True, help_text="Malay title")
    title_zh = serializers.CharField(required=False, allow_blank=True, help_text="Chinese title")
    
    content_text_en = serializers.CharField(required=False, allow_blank=True, help_text="English content")
    content_text_ms = serializers.CharField(required=False, allow_blank=True, help_text="Malay content")
    content_text_zh = serializers.CharField(required=False, allow_blank=True, help_text="Chinese content")
    
    content_images = serializers.ListField(required=False, allow_empty=True, help_text="List of image URLs")
    content_videos = serializers.ListField(required=False, allow_empty=True, help_text="List of video URLs")
    ar_scenario = serializers.PrimaryKeyRelatedField(read_only=True)
    order = serializers.IntegerField(required=False, default=1)
    estimated_time = serializers.IntegerField(required=False, default=30)
    
    class Meta:
        model = Lesson
        fields = ['id', 'chapter', 'title_en', 'title_ms', 'title_zh', 'content_text_en', 'content_text_ms', 'content_text_zh', 
                  'content_images', 'content_videos', 'ar_scenario', 'order', 'estimated_time']
    
    def create(self, validated_data):
        # Extract language fields
        title = {
            'en': validated_data.pop('title_en'),
            'ms': validated_data.pop('title_ms', ''),
            'zh': validated_data.pop('title_zh', ''),
        }
        
        content_text = {
            'en': validated_data.pop('content_text_en', ''),
            'ms': validated_data.pop('content_text_ms', ''),
            'zh': validated_data.pop('content_text_zh', ''),
        }
        
        return Lesson.objects.create(
            title=title,
            content_text=content_text,
            **validated_data
        )
    
    def update(self, instance, validated_data):
        # Extract language fields
        if 'title_en' in validated_data or 'title_ms' in validated_data or 'title_zh' in validated_data:
            title = instance.title or {}
            title['en'] = validated_data.pop('title_en', title.get('en', ''))
            title['ms'] = validated_data.pop('title_ms', title.get('ms', ''))
            title['zh'] = validated_data.pop('title_zh', title.get('zh', ''))
            instance.title = title
        
        if 'content_text_en' in validated_data or 'content_text_ms' in validated_data or 'content_text_zh' in validated_data:
            content_text = instance.content_text or {}
            content_text['en'] = validated_data.pop('content_text_en', content_text.get('en', ''))
            content_text['ms'] = validated_data.pop('content_text_ms', content_text.get('ms', ''))
            content_text['zh'] = validated_data.pop('content_text_zh', content_text.get('zh', ''))
            instance.content_text = content_text
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class LessonProgressSerializer(serializers.ModelSerializer):
    lesson = LessonSerializer(read_only=True)
    
    class Meta:
        model = LessonProgress
        fields = ['id', 'lesson', 'completed', 'time_spent', 'last_viewed', 'completed_at']
        read_only_fields = ['id', 'last_viewed']


class LessonDetailSerializer(serializers.ModelSerializer):
    """Detailed lesson view with progress info"""
    progress = serializers.SerializerMethodField()
    is_completed = serializers.SerializerMethodField()
    ar_scenario_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'content_text', 'content_images', 'content_videos',
            'ar_scenario', 'ar_scenario_info', 'estimated_time', 'order',
            'progress', 'is_completed'
        ]

    def get_ar_scenario_info(self, obj):
        return LessonSerializer(context=self.context).get_ar_scenario_info(obj)
    
    def get_progress(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            try:
                progress = LessonProgress.objects.get(user=user, lesson=obj)
                return LessonProgressSerializer(progress).data
            except LessonProgress.DoesNotExist:
                return None
        return None
    
    def get_is_completed(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            try:
                progress = LessonProgress.objects.get(user=user, lesson=obj)
                return progress.completed
            except LessonProgress.DoesNotExist:
                return False
        return False


# ============================================================================
# PRACTICE & QUIZ SERIALIZERS
# ============================================================================

class PracticeExerciseSerializer(serializers.ModelSerializer):
    title = MultiLanguageField()
    description = MultiLanguageField(required=False, allow_null=True)
    user_best_score = serializers.SerializerMethodField()
    user_attempts = serializers.SerializerMethodField()
    
    class Meta:
        model = PracticeExercise
        fields = ['id', 'chapter', 'title', 'description', 'exercise_type', 'passing_score', 'order', 'user_best_score', 'user_attempts']
        read_only_fields = ['id']
    
    def get_user_best_score(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            attempts = PracticeAttempt.objects.filter(user=user, exercise=obj).order_by('-score')
            if attempts.exists():
                return attempts.first().score
        return None
    
    def get_user_attempts(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return PracticeAttempt.objects.filter(user=user, exercise=obj).count()
        return 0


class PracticeExerciseCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating practice exercises with multi-language support"""
    chapter = serializers.PrimaryKeyRelatedField(queryset=Chapter.objects.all(), required=True)
    
    title_en = serializers.CharField(required=True, help_text="English title")
    title_ms = serializers.CharField(required=False, allow_blank=True, help_text="Malay title")
    title_zh = serializers.CharField(required=False, allow_blank=True, help_text="Chinese title")
    
    description_en = serializers.CharField(required=False, allow_blank=True, default='', help_text="English description")
    description_ms = serializers.CharField(required=False, allow_blank=True, default='', help_text="Malay description")
    description_zh = serializers.CharField(required=False, allow_blank=True, default='', help_text="Chinese description")
    
    exercise_type = serializers.CharField(required=False, default='multiple_choice')
    questions = serializers.ListField(required=False, allow_empty=True)
    passing_score = serializers.IntegerField(required=False, default=70)
    order = serializers.IntegerField(required=False, default=1)
    
    class Meta:
        model = PracticeExercise
        fields = ['id', 'chapter', 'title_en', 'title_ms', 'title_zh', 'description_en', 'description_ms', 'description_zh',
                  'exercise_type', 'questions', 'passing_score', 'order']
    
    def create(self, validated_data):
        title = {
            'en': validated_data.pop('title_en'),
            'ms': validated_data.pop('title_ms', ''),
            'zh': validated_data.pop('title_zh', ''),
        }
        
        description = {
            'en': validated_data.pop('description_en', ''),
            'ms': validated_data.pop('description_ms', ''),
            'zh': validated_data.pop('description_zh', ''),
        }
        
        return PracticeExercise.objects.create(
            title=title,
            description=description,
            **validated_data
        )
    
    def update(self, instance, validated_data):
        if 'title_en' in validated_data or 'title_ms' in validated_data or 'title_zh' in validated_data:
            title = instance.title or {}
            title['en'] = validated_data.pop('title_en', title.get('en', ''))
            title['ms'] = validated_data.pop('title_ms', title.get('ms', ''))
            title['zh'] = validated_data.pop('title_zh', title.get('zh', ''))
            instance.title = title
        
        if 'description_en' in validated_data or 'description_ms' in validated_data or 'description_zh' in validated_data:
            description = instance.description or {}
            description['en'] = validated_data.pop('description_en', description.get('en', ''))
            description['ms'] = validated_data.pop('description_ms', description.get('ms', ''))
            description['zh'] = validated_data.pop('description_zh', description.get('zh', ''))
            instance.description = description
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class PracticeAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = PracticeAttempt
        fields = ['id', 'attempt_number', 'answers', 'score', 'passed', 'completed_at']
        read_only_fields = ['id', 'attempt_number', 'score', 'passed', 'completed_at']
    
    def create(self, validated_data):
        user = self.context['request'].user
        exercise = self.context['exercise']
        attempt_num = PracticeAttempt.objects.filter(user=user, exercise=exercise).count() + 1
        
        return PracticeAttempt.objects.create(
            user=user,
            exercise=exercise,
            attempt_number=attempt_num,
            **validated_data
        )


class QuizSerializer(serializers.ModelSerializer):
    title = MultiLanguageField()
    description = MultiLanguageField(required=False, allow_null=True)
    user_best_score = serializers.SerializerMethodField()
    user_attempts = serializers.SerializerMethodField()
    user_passed = serializers.SerializerMethodField()
    
    class Meta:
        model = Quiz
        fields = ['id', 'chapter', 'title', 'description', 'questions', 'passing_score', 'time_limit', 'show_answers', 'order', 'user_best_score', 'user_attempts', 'user_passed']
        read_only_fields = ['id']
    
    def get_user_best_score(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            attempts = QuizAttempt.objects.filter(user=user, quiz=obj).order_by('-score')
            if attempts.exists():
                return attempts.first().score
        return None
    
    def get_user_attempts(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return QuizAttempt.objects.filter(user=user, quiz=obj).count()
        return 0
    
    def get_user_passed(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return QuizAttempt.objects.filter(user=user, quiz=obj, passed=True).exists()
        return False


class QuizCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating quizzes with multi-language support"""
    chapter = serializers.PrimaryKeyRelatedField(queryset=Chapter.objects.all(), required=True)
    
    title_en = serializers.CharField(required=True, help_text="English title")
    title_ms = serializers.CharField(required=False, allow_blank=True, help_text="Malay title")
    title_zh = serializers.CharField(required=False, allow_blank=True, help_text="Chinese title")
    
    description_en = serializers.CharField(required=False, allow_blank=True, default='', help_text="English description")
    description_ms = serializers.CharField(required=False, allow_blank=True, default='', help_text="Malay description")
    description_zh = serializers.CharField(required=False, allow_blank=True, default='', help_text="Chinese description")
    
    questions = serializers.ListField(required=False, allow_empty=True)
    passing_score = serializers.IntegerField(required=False, default=70)
    time_limit = serializers.IntegerField(required=False, default=0)
    show_answers = serializers.BooleanField(required=False, default=False)
    order = serializers.IntegerField(required=False, default=1)
    
    class Meta:
        model = Quiz
        fields = ['id', 'chapter', 'title_en', 'title_ms', 'title_zh', 'description_en', 'description_ms', 'description_zh',
                  'questions', 'passing_score', 'time_limit', 'show_answers', 'order']
    
    def create(self, validated_data):
        title = {
            'en': validated_data.pop('title_en'),
            'ms': validated_data.pop('title_ms', ''),
            'zh': validated_data.pop('title_zh', ''),
        }
        
        description = {
            'en': validated_data.pop('description_en', ''),
            'ms': validated_data.pop('description_ms', ''),
            'zh': validated_data.pop('description_zh', ''),
        }
        
        return Quiz.objects.create(
            title=title,
            description=description,
            **validated_data
        )
    
    def update(self, instance, validated_data):
        if 'title_en' in validated_data or 'title_ms' in validated_data or 'title_zh' in validated_data:
            title = instance.title or {}
            title['en'] = validated_data.pop('title_en', title.get('en', ''))
            title['ms'] = validated_data.pop('title_ms', title.get('ms', ''))
            title['zh'] = validated_data.pop('title_zh', title.get('zh', ''))
            instance.title = title
        
        if 'description_en' in validated_data or 'description_ms' in validated_data or 'description_zh' in validated_data:
            description = instance.description or {}
            description['en'] = validated_data.pop('description_en', description.get('en', ''))
            description['ms'] = validated_data.pop('description_ms', description.get('ms', ''))
            description['zh'] = validated_data.pop('description_zh', description.get('zh', ''))
            instance.description = description
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class QuizAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAttempt
        fields = ['id', 'attempt_number', 'answers', 'score', 'passed', 'time_spent', 'completed_at']
        read_only_fields = ['id', 'attempt_number', 'score', 'passed', 'completed_at']
    
    def create(self, validated_data):
        user = self.context['request'].user
        quiz = self.context['quiz']
        attempt_num = QuizAttempt.objects.filter(user=user, quiz=quiz).count() + 1
        
        return QuizAttempt.objects.create(
            user=user,
            quiz=quiz,
            attempt_number=attempt_num,
            **validated_data
        )


# ============================================================================
# CHAPTER SERIALIZERS
# ============================================================================

class ChapterProgressSerializer(serializers.ModelSerializer):
    completion_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = ChapterProgress
        fields = [
            'completed_lessons', 'total_lessons',
            'practice_completed', 'practice_score',
            'quiz_completed', 'quiz_score', 'quiz_passed',
            'progress_percentage', 'is_complete', 'completion_percentage'
        ]
    
    def get_completion_percentage(self, obj):
        """Calculate overall chapter completion"""
        lessons_pct = (obj.completed_lessons / obj.total_lessons * 0.4) if obj.total_lessons > 0 else 0
        practice_pct = (0.3 if obj.practice_completed else 0)
        quiz_pct = (0.3 if obj.quiz_passed else 0)
        return lessons_pct + practice_pct + quiz_pct


class ChapterSerializer(serializers.ModelSerializer):
    """List view of chapters"""
    title = MultiLanguageField()
    description = MultiLanguageField(required=False, allow_null=True)
    lessons = LessonSerializer(many=True, read_only=True)
    practice_exercises = PracticeExerciseSerializer(many=True, read_only=True)
    quizzes = QuizSerializer(many=True, read_only=True)
    progress = serializers.SerializerMethodField()
    
    class Meta:
        model = Chapter
        fields = ['id', 'course', 'title', 'description', 'order', 'lessons', 'practice_exercises', 'quizzes', 'progress']
    
    def get_progress(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            try:
                progress = ChapterProgress.objects.get(user=user, chapter=obj)
                return ChapterProgressSerializer(progress).data
            except ChapterProgress.DoesNotExist:
                return None
        return None


class ChapterCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating chapters with multi-language support"""
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all(), required=True)
    
    title_en = serializers.CharField(required=True, help_text="English title")
    title_ms = serializers.CharField(required=False, allow_blank=True, help_text="Malay title")
    title_zh = serializers.CharField(required=False, allow_blank=True, help_text="Chinese title")
    
    description_en = serializers.CharField(required=False, allow_blank=True, help_text="English description")
    description_ms = serializers.CharField(required=False, allow_blank=True, help_text="Malay description")
    description_zh = serializers.CharField(required=False, allow_blank=True, help_text="Chinese description")
    
    class Meta:
        model = Chapter
        fields = ['id', 'course', 'title_en', 'title_ms', 'title_zh', 'description_en', 'description_ms', 'description_zh', 'order']
    
    def create(self, validated_data):
        title = {
            'en': validated_data.pop('title_en'),
            'ms': validated_data.pop('title_ms', ''),
            'zh': validated_data.pop('title_zh', ''),
        }
        
        description = {
            'en': validated_data.pop('description_en', ''),
            'ms': validated_data.pop('description_ms', ''),
            'zh': validated_data.pop('description_zh', ''),
        }
        
        return Chapter.objects.create(
            title=title,
            description=description,
            **validated_data
        )
    
    def update(self, instance, validated_data):
        if 'title_en' in validated_data or 'title_ms' in validated_data or 'title_zh' in validated_data:
            title = instance.title or {}
            title['en'] = validated_data.pop('title_en', title.get('en', ''))
            title['ms'] = validated_data.pop('title_ms', title.get('ms', ''))
            title['zh'] = validated_data.pop('title_zh', title.get('zh', ''))
            instance.title = title
        
        if 'description_en' in validated_data or 'description_ms' in validated_data or 'description_zh' in validated_data:
            description = instance.description or {}
            description['en'] = validated_data.pop('description_en', description.get('en', ''))
            description['ms'] = validated_data.pop('description_ms', description.get('ms', ''))
            description['zh'] = validated_data.pop('description_zh', description.get('zh', ''))
            instance.description = description
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class ChapterDetailSerializer(ChapterSerializer):
    """Detailed chapter view with full content"""
    pass


# ============================================================================
# COURSE & ENROLLMENT SERIALIZERS
# ============================================================================

class CourseEnrollmentSerializer(serializers.ModelSerializer):
    course_title = serializers.JSONField(source='course.title', read_only=True)
    course_code = serializers.CharField(source='course.code', read_only=True)
    course_type = serializers.CharField(source='course.course_type', read_only=True)
    
    class Meta:
        model = CourseEnrollment
        fields = [
            'id',
            'course',
            'course_code',
            'course_type',
            'course_title',
            'status',
            'progress_percentage',
            'final_score',
            'enrollment_date',
            'completed_date',
            'updated_at',
        ]
        read_only_fields = ['id', 'enrollment_date', 'progress_percentage', 'final_score', 'updated_at']


class CourseSerializer(serializers.ModelSerializer):
    """Course catalog listing"""
    title = MultiLanguageField()
    description = MultiLanguageField(required=False, allow_null=True)
    chapters = serializers.SerializerMethodField()
    enrollment_status = serializers.SerializerMethodField()
    prerequisites_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'code', 'title', 'description', 'thumbnail', 'course_type',
            'tags', 'is_published', 'chapters', 'enrollment_status',
            'prerequisites_info'
        ]
    
    def get_chapters(self, obj):
        chapters = Chapter.objects.filter(course=obj).order_by('order')
        return ChapterSerializer(chapters, many=True, context=self.context).data
    
    def get_enrollment_status(self, obj):
        """Get user's enrollment status if authenticated"""
        user = self.context.get('request').user
        if user.is_authenticated:
            try:
                enrollment = CourseEnrollment.objects.get(user=user, course=obj)
                return CourseEnrollmentSerializer(enrollment).data
            except CourseEnrollment.DoesNotExist:
                return None
        return None
    
    def get_prerequisites_info(self, obj):
        """List prerequisite courses with user's completion status"""
        user = self.context.get('request').user
        prereqs = obj.prerequisites.all()
        
        prereq_list = []
        for p in prereqs:
            prereq_item = {
                'id': p.id, 
                'code': p.code, 
                'title': p.title,
                'is_completed': False
            }
            
            # Check if user has completed this prerequisite
            if user and user.is_authenticated:
                is_completed = CourseEnrollment.objects.filter(
                    user=user,
                    course=p,
                    status='completed'
                ).exists()
                prereq_item['is_completed'] = is_completed
            
            prereq_list.append(prereq_item)
        
        return prereq_list


class CourseCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating courses with multi-language support"""
    title_en = serializers.CharField(required=True, help_text="English title")
    title_ms = serializers.CharField(required=False, allow_blank=True, help_text="Malay title")
    title_zh = serializers.CharField(required=False, allow_blank=True, help_text="Chinese title")
    
    description_en = serializers.CharField(required=False, allow_blank=True, help_text="English description")
    description_ms = serializers.CharField(required=False, allow_blank=True, help_text="Malay description")
    description_zh = serializers.CharField(required=False, allow_blank=True, help_text="Chinese description")
    
    class Meta:
        model = Course
        fields = ['id', 'code', 'title_en', 'title_ms', 'title_zh', 'description_en', 'description_ms', 'description_zh',
                  'thumbnail', 'course_type', 'tags', 'is_published', 'prerequisites']
    
    def create(self, validated_data):
        title = {
            'en': validated_data.pop('title_en'),
            'ms': validated_data.pop('title_ms', ''),
            'zh': validated_data.pop('title_zh', ''),
        }
        
        description = {
            'en': validated_data.pop('description_en', ''),
            'ms': validated_data.pop('description_ms', ''),
            'zh': validated_data.pop('description_zh', ''),
        }
        
        return Course.objects.create(
            title=title,
            description=description,
            **validated_data
        )
    
    def update(self, instance, validated_data):
        if 'title_en' in validated_data or 'title_ms' in validated_data or 'title_zh' in validated_data:
            title = instance.title or {}
            title['en'] = validated_data.pop('title_en', title.get('en', ''))
            title['ms'] = validated_data.pop('title_ms', title.get('ms', ''))
            title['zh'] = validated_data.pop('title_zh', title.get('zh', ''))
            instance.title = title
        
        if 'description_en' in validated_data or 'description_ms' in validated_data or 'description_zh' in validated_data:
            description = instance.description or {}
            description['en'] = validated_data.pop('description_en', description.get('en', ''))
            description['ms'] = validated_data.pop('description_ms', description.get('ms', ''))
            description['zh'] = validated_data.pop('description_zh', description.get('zh', ''))
            instance.description = description
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class CourseDetailSerializer(CourseSerializer):
    """Detailed course view with all chapter details"""
    
    def get_prerequisites_info(self, obj):
        """List prerequisite courses with user's completion status"""
        user = self.context.get('request').user
        prereqs = obj.prerequisites.all()
        
        prereq_list = []
        for p in prereqs:
            prereq_item = {
                'id': p.id, 
                'code': p.code, 
                'title': p.title,
                'is_completed': False
            }
            
            # Check if user has completed this prerequisite
            if user and user.is_authenticated:
                is_completed = CourseEnrollment.objects.filter(
                    user=user,
                    course=p,
                    status='completed'
                ).exists()
                prereq_item['is_completed'] = is_completed
            
            prereq_list.append(prereq_item)
        
        return prereq_list


class CourseRegistrationSerializer(serializers.ModelSerializer):
    """For enrolling in a course - with prerequisite validation"""
    error_message = serializers.CharField(read_only=True)
    
    class Meta:
        model = CourseEnrollment
        fields = ['course', 'status', 'error_message']
    
    def validate_course(self, course):
        """Validate that user has met prerequisites"""
        user = self.context.get('request').user
        if not user or not user.is_authenticated:
            raise serializers.ValidationError("User must be authenticated to enroll.")
        
        # Get all prerequisite courses
        prerequisites = course.prerequisites.all()
        
        if prerequisites.exists():
            # Check which prerequisites are completed
            completed_prerequisites = CourseEnrollment.objects.filter(
                user=user,
                course__in=prerequisites,
                status='completed'
            ).values_list('course_id', flat=True)
            
            missing_prerequisites = []
            for prereq in prerequisites:
                if prereq.id not in completed_prerequisites:
                    missing_prerequisites.append(prereq.code)
            
            if missing_prerequisites:
                error_msg = f"You must complete these courses first: {', '.join(missing_prerequisites)}"
                raise serializers.ValidationError(error_msg)
        
        return course
    
    def create(self, validated_data):
        user = self.context['request'].user
        course = validated_data['course']
        
        # Get or create enrollment
        enrollment, created = CourseEnrollment.objects.get_or_create(
            user=user,
            course=course,
            defaults={'status': 'enrolled'}
        )
        
        # If already enrolled, just return (idempotent)
        return enrollment


# ============================================================================
# LEGACY SERIALIZERS (for backwards compatibility)
# ============================================================================

class ModuleSerializer(serializers.ModelSerializer):
    # Virtual fields for frontend
    contentTitle = serializers.SerializerMethodField()
    videoLabel = serializers.SerializerMethodField()
    quizzes = serializers.SerializerMethodField()

    class Meta:
        model = Module
        fields = ['id', 'code', 'title', 'contentTitle', 'content', 'videoLabel', 'quiz', 'quizzes']

    @staticmethod
    def _normalize_correct_answers(quiz_item):
        if not isinstance(quiz_item, dict):
            raise serializers.ValidationError('Each quiz entry must be an object.')

        has_single = 'correctIndex' in quiz_item and quiz_item.get('correctIndex') is not None
        has_multi = 'correctIndexes' in quiz_item and quiz_item.get('correctIndexes') is not None

        if not has_single and not has_multi:
            raise serializers.ValidationError('Each quiz entry must include correctIndex or correctIndexes.')

        if has_multi:
            correct_indexes = quiz_item.get('correctIndexes')
            if not isinstance(correct_indexes, list) or not correct_indexes:
                raise serializers.ValidationError('correctIndexes must be a non-empty list of integers.')
            if len(correct_indexes) > 3:
                raise serializers.ValidationError('A question can have at most 3 correct answers.')
            if not all(isinstance(index, int) and index >= 0 for index in correct_indexes):
                raise serializers.ValidationError('correctIndexes must contain non-negative integers only.')
        else:
            single_index = quiz_item.get('correctIndex')
            if not isinstance(single_index, int) or single_index < 0:
                raise serializers.ValidationError('correctIndex must be a non-negative integer.')
            correct_indexes = [single_index]

        unique_indexes = sorted(set(correct_indexes))
        if len(unique_indexes) != len(correct_indexes):
            raise serializers.ValidationError('correctIndexes cannot contain duplicate values.')

        if len(unique_indexes) == 1:
            quiz_item['correctIndex'] = unique_indexes[0]
        else:
            quiz_item.pop('correctIndex', None)
        quiz_item['correctIndexes'] = unique_indexes
        return quiz_item

    @classmethod
    def _normalize_quiz_payload(cls, value):
        if value in (None, ''):
            return []
        if isinstance(value, dict):
            return [cls._normalize_correct_answers(value)]
        if isinstance(value, list):
            normalized = []
            for quiz_item in value:
                normalized.append(cls._normalize_correct_answers(quiz_item))
            return normalized
        raise serializers.ValidationError('Quiz data must be an object or a list of objects.')

    def to_internal_value(self, data):
        mutable_data = data.copy()

        if 'quizzes' in mutable_data:
            mutable_data['quiz'] = mutable_data.get('quizzes')

        return super().to_internal_value(mutable_data)

    def validate_quiz(self, value):
        return self._normalize_quiz_payload(value)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        normalized_quizzes = self._normalize_quiz_payload(instance.quiz)
        representation['quizzes'] = normalized_quizzes
        representation['quiz'] = normalized_quizzes[0] if normalized_quizzes else None
        return representation

    def get_contentTitle(self, obj):
        return getattr(obj, 'contentTitle', 'Module Content')

    def get_videoLabel(self, obj):
        return getattr(obj, 'videoLabel', 'Watch Video')

    def get_quizzes(self, obj):
        return self._normalize_quiz_payload(obj.quiz)

class ModuleProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuleProgress
        fields = ['id', 'user', 'module', 'completed', 'completed_at']
        read_only_fields = ['id', 'user', 'completed_at']


class CourseProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseProgress
        fields = ['id', 'user', 'course', 'completed_modules', 'total_modules', 'progress', 'completed', 'updated_at']
        read_only_fields = ['id', 'user', 'updated_at']
