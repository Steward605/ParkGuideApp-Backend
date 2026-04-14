# Complete rewrite - Simplified multi-language serializers
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Course, Chapter, Lesson, PracticeExercise, Quiz,
    CourseEnrollment, CourseProgress
)

User = get_user_model()


# ============================================================================
# SIMPLIFIED MULTI-LANGUAGE HANDLING
# ============================================================================

class MultiLangSerializer(serializers.Serializer):
    """Base mixin for handling multilingual fields (en, ms, zh)"""
    
    def _build_json_field(self, data, field_name):
        """Build {en, ms, zh} JSON from separate language fields"""
        return {
            'en': data.get(f'{field_name}_en', ''),
            'ms': data.get(f'{field_name}_ms', ''),
            'zh': data.get(f'{field_name}_zh', ''),
        }
    
    def _extract_lang_fields(self, validated_data, field_name):
        """Extract language fields from validated data and build JSON"""
        json_value = {
            'en': validated_data.pop(f'{field_name}_en', ''),
            'ms': validated_data.pop(f'{field_name}_ms', ''),
            'zh': validated_data.pop(f'{field_name}_zh', ''),
        }
        # Remove any empty fields to keep it clean
        return {k: v for k, v in json_value.items() if v}


# ============================================================================
# LESSON SERIALIZERS
# ============================================================================

class LessonCreateSerializer(MultiLangSerializer, serializers.ModelSerializer):
    """Create lessons with multi-language support - form inputs"""
    
    # Multi-language inputs
    title_en = serializers.CharField(required=True, allow_blank=False)
    title_ms = serializers.CharField(required=False, allow_blank=True)
    title_zh = serializers.CharField(required=False, allow_blank=True)
    
    content_text_en = serializers.CharField(required=False, allow_blank=True)
    content_text_ms = serializers.CharField(required=False, allow_blank=True)
    content_text_zh = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = Lesson
        fields = [
            'id',
            'title_en', 'title_ms', 'title_zh',
            'content_text_en', 'content_text_ms', 'content_text_zh',
            'content_images', 'content_videos',
            'order', 'estimated_time'
        ]
        extra_kwargs = {
            'content_images': {'required': False},
            'content_videos': {'required': False},
            'order': {'required': False},
            'estimated_time': {'required': False},
        }
    
    def create(self, validated_data):
        """Create lesson with JSON multilingual fields"""
        # Build title JSON
        title = self._extract_lang_fields(validated_data, 'title')
        
        # Build content_text JSON
        content_text = self._extract_lang_fields(validated_data, 'content_text')
        
        return Lesson.objects.create(
            title=title,
            content_text=content_text,
            **validated_data
        )
    
    def update(self, instance, validated_data):
        """Update lesson with JSON multilingual fields"""
        # Update title if any language field provided
        if any(k.startswith('title_') for k in validated_data.keys()):
            title = self._extract_lang_fields(validated_data, 'title')
            instance.title = {**(instance.title or {}), **title}
        
        # Update content_text if any language field provided
        if any(k.startswith('content_text_') for k in validated_data.keys()):
            content_text = self._extract_lang_fields(validated_data, 'content_text')
            instance.content_text = {**(instance.content_text or {}), **content_text}
        
        # Update other fields
        for attr, value in validated_data.items():
            if not attr.startswith(('title_', 'content_text_')):
                setattr(instance, attr, value)
        
        instance.save()
        return instance


class LessonSerializer(serializers.ModelSerializer):
    """Read-only lesson serializer"""
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'chapter', 'title', 'content_text', 
            'content_images', 'content_videos', 'order', 'estimated_time'
        ]
        read_only_fields = ['id', 'chapter']


# ============================================================================
# PRACTICE EXERCISE SERIALIZERS
# ============================================================================

class PracticeExerciseCreateSerializer(MultiLangSerializer, serializers.ModelSerializer):
    """Create practice exercises with multi-language support"""
    
    # Multi-language inputs
    title_en = serializers.CharField(required=True, allow_blank=False)
    title_ms = serializers.CharField(required=False, allow_blank=True)
    title_zh = serializers.CharField(required=False, allow_blank=True)
    
    description_en = serializers.CharField(required=False, allow_blank=True)
    description_ms = serializers.CharField(required=False, allow_blank=True)
    description_zh = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = PracticeExercise
        fields = [
            'id',
            'title_en', 'title_ms', 'title_zh',
            'description_en', 'description_ms', 'description_zh',
            'exercise_type', 'questions',
            'passing_score', 'order'
        ]
        extra_kwargs = {
            'exercise_type': {'required': False},
            'questions': {'required': False},  # Provide default
            'passing_score': {'required': False},
            'order': {'required': False},
        }
    
    def create(self, validated_data):
        """Create exercise with JSON multilingual fields"""
        # Build title JSON
        title = self._extract_lang_fields(validated_data, 'title')
        
        # Build description JSON
        description = self._extract_lang_fields(validated_data, 'description')
        
        # Ensure questions has default
        if 'questions' not in validated_data or not validated_data['questions']:
            validated_data['questions'] = []
        
        return PracticeExercise.objects.create(
            title=title,
            description=description,
            **validated_data
        )
    
    def update(self, instance, validated_data):
        """Update exercise with JSON multilingual fields"""
        if any(k.startswith('title_') for k in validated_data.keys()):
            title = self._extract_lang_fields(validated_data, 'title')
            instance.title = {**(instance.title or {}), **title}
        
        if any(k.startswith('description_') for k in validated_data.keys()):
            description = self._extract_lang_fields(validated_data, 'description')
            instance.description = {**(instance.description or {}), **description}
        
        for attr, value in validated_data.items():
            if not attr.startswith(('title_', 'description_')):
                setattr(instance, attr, value)
        
        instance.save()
        return instance


class PracticeExerciseSerializer(serializers.ModelSerializer):
    """Read-only practice exercise serializer"""
    
    class Meta:
        model = PracticeExercise
        fields = [
            'id', 'chapter', 'title', 'description',
            'exercise_type', 'questions', 'passing_score', 'order'
        ]
        read_only_fields = ['id', 'chapter']


# ============================================================================
# QUIZ SERIALIZERS
# ============================================================================

class QuizCreateSerializer(MultiLangSerializer, serializers.ModelSerializer):
    """Create quizzes with multi-language support"""
    
    # Multi-language inputs
    title_en = serializers.CharField(required=True, allow_blank=False)
    title_ms = serializers.CharField(required=False, allow_blank=True)
    title_zh = serializers.CharField(required=False, allow_blank=True)
    
    description_en = serializers.CharField(required=False, allow_blank=True)
    description_ms = serializers.CharField(required=False, allow_blank=True)
    description_zh = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = Quiz
        fields = [
            'id',
            'title_en', 'title_ms', 'title_zh',
            'description_en', 'description_ms', 'description_zh',
            'questions', 'passing_score',
            'time_limit', 'show_answers', 'order'
        ]
        extra_kwargs = {
            'questions': {'required': False},  # Provide default
            'passing_score': {'required': False},
            'time_limit': {'required': False},
            'show_answers': {'required': False},
            'order': {'required': False},
        }
    
    def create(self, validated_data):
        """Create quiz with JSON multilingual fields"""
        # Build title JSON
        title = self._extract_lang_fields(validated_data, 'title')
        
        # Build description JSON
        description = self._extract_lang_fields(validated_data, 'description')
        
        # Ensure questions has default
        if 'questions' not in validated_data or not validated_data['questions']:
            validated_data['questions'] = []
        
        return Quiz.objects.create(
            title=title,
            description=description,
            **validated_data
        )
    
    def update(self, instance, validated_data):
        """Update quiz with JSON multilingual fields"""
        if any(k.startswith('title_') for k in validated_data.keys()):
            title = self._extract_lang_fields(validated_data, 'title')
            instance.title = {**(instance.title or {}), **title}
        
        if any(k.startswith('description_') for k in validated_data.keys()):
            description = self._extract_lang_fields(validated_data, 'description')
            instance.description = {**(instance.description or {}), **description}
        
        for attr, value in validated_data.items():
            if not attr.startswith(('title_', 'description_')):
                setattr(instance, attr, value)
        
        instance.save()
        return instance


class QuizSerializer(serializers.ModelSerializer):
    """Read-only quiz serializer"""
    
    class Meta:
        model = Quiz
        fields = [
            'id', 'chapter', 'title', 'description',
            'questions', 'passing_score',
            'time_limit', 'show_answers', 'order'
        ]
        read_only_fields = ['id', 'chapter']


# ============================================================================
# CHAPTER SERIALIZERS
# ============================================================================

class ChapterCreateSerializer(MultiLangSerializer, serializers.ModelSerializer):
    """Create chapters with multi-language support"""
    
    title_en = serializers.CharField(required=True, allow_blank=False)
    title_ms = serializers.CharField(required=False, allow_blank=True)
    title_zh = serializers.CharField(required=False, allow_blank=True)
    
    description_en = serializers.CharField(required=False, allow_blank=True)
    description_ms = serializers.CharField(required=False, allow_blank=True)
    description_zh = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = Chapter
        fields = [
            'id',
            'title_en', 'title_ms', 'title_zh',
            'description_en', 'description_ms', 'description_zh',
            'order', 'code'
        ]
        extra_kwargs = {
            'order': {'required': False},
            'code': {'required': False},
        }
    
    def create(self, validated_data):
        title = self._extract_lang_fields(validated_data, 'title')
        description = self._extract_lang_fields(validated_data, 'description')
        
        return Chapter.objects.create(
            title=title,
            description=description,
            **validated_data
        )
    
    def update(self, instance, validated_data):
        if any(k.startswith('title_') for k in validated_data.keys()):
            title = self._extract_lang_fields(validated_data, 'title')
            instance.title = {**(instance.title or {}), **title}
        
        if any(k.startswith('description_') for k in validated_data.keys()):
            description = self._extract_lang_fields(validated_data, 'description')
            instance.description = {**(instance.description or {}), **description}
        
        for attr, value in validated_data.items():
            if not attr.startswith(('title_', 'description_')):
                setattr(instance, attr, value)
        
        instance.save()
        return instance


class ChapterSerializer(serializers.ModelSerializer):
    """Read-only chapter serializer"""
    
    class Meta:
        model = Chapter
        fields = ['id', 'course', 'title', 'description', 'order', 'code']
        read_only_fields = ['id', 'course']


# ============================================================================
# COURSE SERIALIZERS
# ============================================================================

class CourseCreateSerializer(MultiLangSerializer, serializers.ModelSerializer):
    """Create courses with multi-language support"""
    
    title_en = serializers.CharField(required=True, allow_blank=False)
    title_ms = serializers.CharField(required=False, allow_blank=True)
    title_zh = serializers.CharField(required=False, allow_blank=True)
    
    description_en = serializers.CharField(required=False, allow_blank=True)
    description_ms = serializers.CharField(required=False, allow_blank=True)
    description_zh = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = Course
        fields = [
            'id', 'code',
            'title_en', 'title_ms', 'title_zh',
            'description_en', 'description_ms', 'description_zh',
            'thumbnail', 'is_published'
        ]
        extra_kwargs = {
            'code': {'required': False},
            'thumbnail': {'required': False},
            'is_published': {'required': False},
        }
    
    def create(self, validated_data):
        title = self._extract_lang_fields(validated_data, 'title')
        description = self._extract_lang_fields(validated_data, 'description')
        
        return Course.objects.create(
            title=title,
            description=description,
            **validated_data
        )
    
    def update(self, instance, validated_data):
        if any(k.startswith('title_') for k in validated_data.keys()):
            title = self._extract_lang_fields(validated_data, 'title')
            instance.title = {**(instance.title or {}), **title}
        
        if any(k.startswith('description_') for k in validated_data.keys()):
            description = self._extract_lang_fields(validated_data, 'description')
            instance.description = {**(instance.description or {}), **description}
        
        for attr, value in validated_data.items():
            if not attr.startswith(('title_', 'description_')):
                setattr(instance, attr, value)
        
        instance.save()
        return instance


class CourseSerializer(serializers.ModelSerializer):
    """Read-only course serializer"""
    
    class Meta:
        model = Course
        fields = [
            'id', 'code', 'title', 'description',
            'thumbnail', 'is_published', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
