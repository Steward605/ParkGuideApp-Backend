"""
Fresh, clean serializers for the course API
Simplified multi-language handling and proper validation
"""
from rest_framework import serializers
from urllib.parse import urlparse
from courses.models import (
    Course, Chapter, Lesson, PracticeExercise, Quiz,
    LessonProgress, PracticeAttempt, QuizAttempt, CourseEnrollment
)
from courses.prerequisite_utils import get_effective_prerequisite_courses


# ============================================================================
# CORE SERIALIZERS - Simple, Clean, Focused
# ============================================================================

def _coerce_multilingual_text(value):
    """Normalize quiz/practice text into {en, ms, zh} or a plain string."""
    if isinstance(value, dict):
        if any(key in value for key in ('en', 'ms', 'zh')):
            return value
        if 'text' in value:
            return _coerce_multilingual_text(value['text'])
        if 'question' in value:
            return _coerce_multilingual_text(value['question'])
    return value


def _normalize_practice_questions(questions):
    normalized = []
    for item in questions or []:
        if not isinstance(item, dict):
            continue

        raw_options = item.get('options', [])
        if isinstance(raw_options, dict):
            raw_options = raw_options.get('en') or next(iter(raw_options.values()), [])

        options = []
        for option in raw_options or []:
            text = _coerce_multilingual_text(option)
            if isinstance(text, dict):
                text = text.get('en') or next(iter(text.values()), '')
            options.append(text)

        correct_indexes = item.get('correctIndexes')
        correct_index = item.get('correctIndex')
        if correct_indexes is None and isinstance(raw_options, list):
            derived_indexes = [
                idx for idx, option in enumerate(raw_options)
                if isinstance(option, dict) and option.get('is_correct')
            ]
            if derived_indexes:
                correct_indexes = derived_indexes
        if correct_index is None and isinstance(correct_indexes, list) and correct_indexes:
            correct_index = correct_indexes[0]

        normalized.append({
            'question': item.get('question') or item.get('text') or item.get('question_text') or '',
            'options': options,
            'correctIndex': correct_index,
            'correctIndexes': correct_indexes,
            'explanation': item.get('explanation', ''),
        })

    return normalized


def _normalize_quiz_questions(questions):
    normalized = []
    for item in questions or []:
        if not isinstance(item, dict):
            continue

        raw_options = item.get('options', [])
        if isinstance(raw_options, dict):
            option_sets = raw_options
            english_options = option_sets.get('en') or next(iter(option_sets.values()), [])
            raw_options = [
                {
                    'text': {
                        lang: values[idx] if isinstance(values, list) and idx < len(values) else ''
                        for lang, values in option_sets.items()
                    }
                }
                for idx in range(len(english_options))
            ]

        correct_indexes = item.get('correctIndexes')
        correct_index = item.get('correctIndex')
        if correct_indexes is None and isinstance(raw_options, list):
            derived_indexes = [
                idx for idx, option in enumerate(raw_options)
                if isinstance(option, dict) and option.get('is_correct')
            ]
            if derived_indexes:
                correct_indexes = derived_indexes
        if correct_indexes is None and correct_index is not None:
            correct_indexes = [correct_index]
        if correct_index is None and isinstance(correct_indexes, list) and correct_indexes:
            correct_index = correct_indexes[0]

        options = []
        for idx, option in enumerate(raw_options or []):
            text = _coerce_multilingual_text(option)
            if not isinstance(text, dict):
                text = {'en': text}
            options.append({
                'text': text,
                'is_correct': idx in (correct_indexes or []),
            })

        normalized.append({
            'question_text': _coerce_multilingual_text(
                item.get('question_text') or item.get('question') or item.get('text') or ''
            ),
            'options': options,
            'correctIndex': correct_index,
            'correctIndexes': correct_indexes,
            'explanation': item.get('explanation', ''),
        })

    return normalized


class CourseThumbnailMixin:
    def _get_thumbnail_url(self, obj):
        """Return a safe thumbnail URL or a local fallback."""
        thumbnail = obj.thumbnail
        fallback_path = '/static/images/icon.png'

        if thumbnail:
            parsed = urlparse(thumbnail)
            if parsed.netloc != 'images.unsplash.com':
                return thumbnail

        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(fallback_path)
        return fallback_path

class CourseEnrollmentSerializer(serializers.ModelSerializer):
    """Enrollment payload used by the active API"""
    course_title = serializers.SerializerMethodField()

    class Meta:
        model = CourseEnrollment
        fields = [
            'id', 'course', 'course_title', 'status', 'progress_percentage',
            'final_score', 'enrollment_date', 'completed_date', 'updated_at'
        ]
        read_only_fields = fields

    def get_course_title(self, obj):
        return obj.course.title


class LessonSerializer(serializers.ModelSerializer):
    """Basic lesson data"""
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = ['id', 'chapter', 'title', 'content_text', 'content_images', 
                  'content_videos', 'order', 'estimated_time', 'progress']
        read_only_fields = ['id', 'chapter', 'order']

    def get_progress(self, obj):
        """Get user's lesson progress if authenticated"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                progress = LessonProgress.objects.get(lesson=obj, user=request.user)
                return {
                    'completed': progress.completed,
                    'completed_at': progress.completed_at,
                    'time_spent': progress.time_spent,
                    'last_viewed': progress.last_viewed,
                }
            except LessonProgress.DoesNotExist:
                return None
        return None


class PracticeExerciseSerializer(serializers.ModelSerializer):
    """Practice exercise with submissions"""
    user_best_score = serializers.SerializerMethodField()
    user_attempts = serializers.SerializerMethodField()
    questions = serializers.SerializerMethodField()

    class Meta:
        model = PracticeExercise
        fields = ['id', 'chapter', 'title', 'description', 'exercise_type', 
                  'questions', 'passing_score', 'order', 'user_best_score', 'user_attempts']
        read_only_fields = ['id', 'chapter', 'order', 'questions']

    def get_questions(self, obj):
        return _normalize_practice_questions(obj.questions)

    def get_user_best_score(self, obj):
        """Get user's best score"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            attempts = PracticeAttempt.objects.filter(
                exercise=obj, user=request.user
            ).order_by('-score')
            if attempts.exists():
                return attempts.first().score
        return None

    def get_user_attempts(self, obj):
        """Get user's attempt count"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return PracticeAttempt.objects.filter(
                exercise=obj, user=request.user
            ).count()
        return 0


class QuizSerializer(serializers.ModelSerializer):
    """Quiz with submission tracking"""
    user_best_score = serializers.SerializerMethodField()
    user_attempts = serializers.SerializerMethodField()
    user_passed = serializers.SerializerMethodField()
    questions = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = ['id', 'chapter', 'title', 'description', 'questions', 
                  'passing_score', 'time_limit', 'show_answers', 'order',
                  'user_best_score', 'user_attempts', 'user_passed']
        read_only_fields = ['id', 'chapter', 'order', 'questions']

    def get_questions(self, obj):
        return _normalize_quiz_questions(obj.questions)

    def get_user_best_score(self, obj):
        """Get user's best quiz score"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            attempts = QuizAttempt.objects.filter(
                quiz=obj, user=request.user
            ).order_by('-score')
            if attempts.exists():
                return attempts.first().score
        return None

    def get_user_attempts(self, obj):
        """Get user's attempt count"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return QuizAttempt.objects.filter(
                quiz=obj, user=request.user
            ).count()
        return 0

    def get_user_passed(self, obj):
        """Check if user passed"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            attempts = QuizAttempt.objects.filter(
                quiz=obj, user=request.user, passed=True
            )
            return attempts.exists()
        return False


class ChapterDetailSerializer(serializers.ModelSerializer):
    """Full chapter with all nested content"""
    lessons = LessonSerializer(many=True, read_only=True)
    practice_exercises = PracticeExerciseSerializer(many=True, read_only=True)
    quizzes = QuizSerializer(many=True, read_only=True)

    class Meta:
        model = Chapter
        fields = ['id', 'course', 'title', 'description', 'order', 
                  'lessons', 'practice_exercises', 'quizzes']
        read_only_fields = ['id', 'course', 'order']


class ChapterListSerializer(serializers.ModelSerializer):
    """Minimal chapter info for lists"""
    lesson_count = serializers.SerializerMethodField()

    class Meta:
        model = Chapter
        fields = ['id', 'course', 'title', 'order', 'lesson_count']
        read_only_fields = ['id', 'course', 'order']

    def get_lesson_count(self, obj):
        return obj.lessons.count()


class CourseDetailSerializer(CourseThumbnailMixin, serializers.ModelSerializer):
    """Full course with all chapters and content"""
    chapters = ChapterDetailSerializer(many=True, read_only=True)
    chapter_count = serializers.SerializerMethodField()
    enrollment_status = serializers.SerializerMethodField()
    prerequisites_info = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'code', 'title', 'description', 'thumbnail', 
                  'is_published', 'chapter_count', 'chapters',
                  'enrollment_status', 'prerequisites_info']
        read_only_fields = ['id', 'chapter_count']

    def get_chapter_count(self, obj):
        return obj.chapters.count()

    def get_thumbnail(self, obj):
        return self._get_thumbnail_url(obj)

    def get_enrollment_status(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            enrollment = CourseEnrollment.objects.filter(
                user=request.user,
                course=obj,
            ).first()
            if enrollment:
                return CourseEnrollmentSerializer(enrollment).data
        return None

    def get_prerequisites_info(self, obj):
        request = self.context.get('request')
        user = request.user if request else None
        prereqs = []

        for course in get_effective_prerequisite_courses(obj):
            is_completed = False
            if user and user.is_authenticated:
                is_completed = CourseEnrollment.objects.filter(
                    user=user,
                    course=course,
                    status='completed',
                ).exists()

            prereqs.append({
                'id': course.id,
                'code': course.code,
                'title': course.title,
                'is_completed': is_completed,
            })

        return prereqs


class CourseListSerializer(CourseThumbnailMixin, serializers.ModelSerializer):
    """Course listing with summary info"""
    chapter_count = serializers.SerializerMethodField()
    enrollment_status = serializers.SerializerMethodField()
    prerequisites_info = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'code', 'title', 'description', 'thumbnail', 
                  'is_published', 'chapter_count', 'enrollment_status',
                  'prerequisites_info']
        read_only_fields = ['id']

    def get_chapter_count(self, obj):
        return obj.chapters.count()

    def get_thumbnail(self, obj):
        return self._get_thumbnail_url(obj)

    def get_enrollment_status(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            enrollment = CourseEnrollment.objects.filter(
                user=request.user,
                course=obj,
            ).first()
            if enrollment:
                return CourseEnrollmentSerializer(enrollment).data
        return None

    def get_prerequisites_info(self, obj):
        request = self.context.get('request')
        user = request.user if request else None
        prereqs = []

        for course in get_effective_prerequisite_courses(obj):
            is_completed = False
            if user and user.is_authenticated:
                is_completed = CourseEnrollment.objects.filter(
                    user=user,
                    course=course,
                    status='completed',
                ).exists()

            prereqs.append({
                'id': course.id,
                'code': course.code,
                'title': course.title,
                'is_completed': is_completed,
            })

        return prereqs


class CourseCreateUpdateSerializer(serializers.ModelSerializer):
    """Create/Update course"""
    class Meta:
        model = Course
        fields = ['code', 'title', 'description', 'thumbnail', 'is_published']

    def validate_code(self, value):
        """Code must be unique"""
        if self.instance is None:  # Creating
            if Course.objects.filter(code=value).exists():
                raise serializers.ValidationError("Course with this code already exists")
        return value


class ChapterCreateUpdateSerializer(serializers.ModelSerializer):
    """Create/Update chapter"""
    class Meta:
        model = Chapter
        fields = ['title', 'description', 'order']

    def validate_order(self, value):
        """Order must be positive"""
        if value < 1:
            raise serializers.ValidationError("Order must be 1 or greater")
        return value


class LessonCreateUpdateSerializer(serializers.ModelSerializer):
    """Create/Update lesson with multilingual content support
    
    Example multilingual lesson payload:
    {
        "title": {"en": "Python Basics", "ms": "Asas Python", "zh": "Python基础"},
        "content_text": {"en": "# Introduction to Python...", "ms": "# Pengenalan Python...", "zh": "# Python简介..."},
        "content_images": [
            {"url": "https://example.com/image1.jpg", "caption": {"en": "Code example", "ms": "Contoh kod", "zh": "代码示例"}},
            {"url": "https://example.com/image2.jpg", "caption": {}}
        ],
        "content_videos": [
            {
                "url": "https://youtube.com/watch?v=xyz",
                "title": {"en": "Python Tutorial", "ms": "Tutorial Python", "zh": "Python教程"},
                "description": {"en": "Basic concepts", "ms": "Konsep asas", "zh": "基本概念"},
                "duration": 600
            }
        ],
        "order": 1,
        "estimated_time": 45
    }
    
    All text fields (title, content_text, video titles/descriptions, image captions) 
    should be objects with language codes as keys: {en, ms, zh}
    """
    class Meta:
        model = Lesson
        fields = ['title', 'content_text', 'content_images', 'content_videos', 
                  'order', 'estimated_time']

    def validate_estimated_time(self, value):
        """Time must be positive"""
        if value < 1:
            raise serializers.ValidationError("Estimated time must be 1 or greater")
        return value


class PracticeExerciseCreateUpdateSerializer(serializers.ModelSerializer):
    """Create/Update exercise with multiple questions support"""
    questions = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_empty=True,
        help_text="Array of questions: [{text, options[], correctIndex/correctIndexes, explanation}]"
    )
    chapter = serializers.PrimaryKeyRelatedField(
        queryset=Chapter.objects.all(),
        required=False,
        help_text="Chapter ID - required for creation"
    )
    
    class Meta:
        model = PracticeExercise
        fields = ['id', 'chapter', 'title', 'description', 'exercise_type', 'questions', 
                  'passing_score', 'order']
        read_only_fields = ['id']

    def validate_chapter(self, value):
        """Chapter is required for creation"""
        if self.instance is None and value is None:
            if not isinstance(self.initial_data, dict) or 'chapter' not in self.initial_data:
                raise serializers.ValidationError("Chapter is required when creating an exercise")
        return value

    def validate_questions(self, value):
        """Validate questions array structure for multiple questions
        
        Each question should follow this multilingual structure:
        {
            "text": {"en": "What is Python?", "ms": "Apa itu Python?", "zh": "Python是什么?"},
            "options": [
                {
                    "text": {"en": "A programming language", "ms": "Bahasa pemrograman", "zh": "编程语言"},
                    "is_correct": true,
                    "explanation": {"en": "Correct! Python is...", "ms": "Betul! Python ialah...", "zh": "正确！Python是..."}
                },
                {
                    "text": {"en": "A type of snake", "ms": "Sejenis ular", "zh": "一种蛇"},
                    "is_correct": false
                }
            ],
            "correctIndex": 0,  // For single-answer questions
            "correctIndexes": [0],  // For multi-answer questions (optional)
            "explanation": {"en": "Python is a server-side...", "ms": "Python ialah bahasa sisi pelayan...", "zh": "Python是一种服务器端..."}
        }
        """
        if value is None:
            return []
        if not isinstance(value, list):
            raise serializers.ValidationError("Questions must be an array")
        
        # Validate each question has required fields
        for idx, question in enumerate(value):
            if not isinstance(question, dict):
                raise serializers.ValidationError(f"Question {idx} must be an object")
            if 'text' not in question and 'question' not in question:
                raise serializers.ValidationError(f"Question {idx} missing text/question field")
            if 'options' not in question:
                raise serializers.ValidationError(f"Question {idx} missing options array")
            if 'correctIndex' not in question and 'correctIndexes' not in question:
                raise serializers.ValidationError(f"Question {idx} missing correctIndex/correctIndexes")
        
        return value

    def create(self, validated_data):
        """Create exercise with proper chapter assignment"""
        chapter = validated_data.pop('chapter', None)
        if chapter is None:
            raise serializers.ValidationError("Chapter is required")
        
        return PracticeExercise.objects.create(chapter=chapter, **validated_data)

    def update(self, instance, validated_data):
        """Update exercise, allowing questions to be modified"""
        validated_data.pop('chapter', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class QuizCreateUpdateSerializer(serializers.ModelSerializer):
    """Create/Update quiz with questions support"""
    questions = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_empty=True,
        help_text="Array of questions: [{text, options[], correctIndex/correctIndexes, explanation}]"
    )
    chapter = serializers.PrimaryKeyRelatedField(
        queryset=Chapter.objects.all(),
        required=False,
        help_text="Chapter ID - required for creation"
    )
    
    class Meta:
        model = Quiz
        fields = ['id', 'chapter', 'title', 'description', 'questions', 'passing_score', 
                  'time_limit', 'show_answers', 'order']
        read_only_fields = ['id']

    def validate_chapter(self, value):
        """Chapter is required for creation"""
        if self.instance is None and value is None:
            # Check if chapter is in request data
            if not isinstance(self.initial_data, dict) or 'chapter' not in self.initial_data:
                raise serializers.ValidationError("Chapter is required when creating a quiz")
        return value

    def validate_questions(self, value):
        """Validate questions array structure for multiple questions
        
        Each question should follow this multilingual structure:
        {
            "text": {"en": "What is Python?", "ms": "Apa itu Python?", "zh": "Python是什么?"},
            "options": [
                {
                    "text": {"en": "A programming language", "ms": "Bahasa pemrograman", "zh": "编程语言"},
                    "is_correct": true,
                    "explanation": {"en": "Correct! Python is...", "ms": "Betul! Python ialah...", "zh": "正确！Python是..."}
                },
                {
                    "text": {"en": "A type of snake", "ms": "Sejenis ular", "zh": "一种蛇"},
                    "is_correct": false
                }
            ],
            "correctIndex": 0,  // For single-answer questions
            "correctIndexes": [0],  // For multi-answer questions (optional)
            "explanation": {"en": "Python is a server-side...", "ms": "Python ialah bahasa sisi pelayan...", "zh": "Python是一种服务器端..."}
        }
        
        For quizzes, you can also include time_limit and show_answers fields.
        """
        if value is None:
            return []
        if not isinstance(value, list):
            raise serializers.ValidationError("Questions must be an array")
        
        # Validate each question has required fields
        for idx, question in enumerate(value):
            if not isinstance(question, dict):
                raise serializers.ValidationError(f"Question {idx} must be an object")
            if 'text' not in question and 'question' not in question:
                raise serializers.ValidationError(f"Question {idx} missing text/question field")
            if 'options' not in question:
                raise serializers.ValidationError(f"Question {idx} missing options array")
            if 'correctIndex' not in question and 'correctIndexes' not in question:
                raise serializers.ValidationError(f"Question {idx} missing correctIndex/correctIndexes")
        
        return value

    def create(self, validated_data):
        """Create quiz with proper chapter assignment"""
        # Chapter may come from URL or request data
        chapter = validated_data.pop('chapter', None)
        if chapter is None:
            raise serializers.ValidationError("Chapter is required")
        
        return Quiz.objects.create(chapter=chapter, **validated_data)

    def update(self, instance, validated_data):
        """Update quiz, allowing questions to be modified"""
        # Don't change chapter on update
        validated_data.pop('chapter', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
