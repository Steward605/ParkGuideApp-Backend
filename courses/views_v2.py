# Complete rewrite - Simplified multi-language views
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction

from .models import (
    Course, Chapter, Lesson, PracticeExercise, Quiz,
    CourseEnrollment, CourseProgress
)
from .serializers_v2 import (
    CourseCreateSerializer, CourseSerializer,
    ChapterCreateSerializer, ChapterSerializer,
    LessonCreateSerializer, LessonSerializer,
    PracticeExerciseCreateSerializer, PracticeExerciseSerializer,
    QuizCreateSerializer, QuizSerializer,
)


# ============================================================================
# PERMISSION CLASSES
# ============================================================================

class IsInstructor(permissions.BasePermission):
    """Only instructors can edit courses"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.user_type == 'instructor'


class IsEnrolled(permissions.BasePermission):
    """Only enrolled students can view course content"""
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_authenticated:
            return CourseEnrollment.objects.filter(user=request.user, course=obj).exists()
        return False


# ============================================================================
# COURSE VIEWSET
# ============================================================================

class CourseViewSet(viewsets.ModelViewSet):
    """
    Course management with multi-language support
    
    POST /api/courses/ - Create course (instructor only)
    GET /api/courses/ - List all published courses
    GET /api/courses/{id}/ - Get course details
    PUT /api/courses/{id}/ - Update course (instructor only)
    DELETE /api/courses/{id}/ - Delete course (instructor only)
    """
    
    queryset = Course.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CourseCreateSerializer
        return CourseSerializer
    
    def get_queryset(self):
        if self.request.user and self.request.user.user_type == 'instructor':
            # Instructors see all their courses
            return Course.objects.all()
        # Students only see published courses
        return Course.objects.filter(is_published=True)
    
    def create(self, request, *args, **kwargs):
        """Create a new course (instructor only)"""
        if request.user.user_type != 'instructor':
            return Response(
                {'error': 'Only instructors can create courses'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Update course (instructor only)"""
        if request.user.user_type != 'instructor':
            return Response(
                {'error': 'Only instructors can update courses'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Delete course (instructor only)"""
        if request.user.user_type != 'instructor':
            return Response(
                {'error': 'Only instructors can delete courses'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def enroll(self, request, pk=None):
        """Enroll current user in course"""
        course = self.get_object()
        user = request.user
        
        enrollment, created = CourseEnrollment.objects.get_or_create(
            user=user,
            course=course
        )
        
        if created:
            return Response(
                {'message': f'Successfully enrolled in {course.title}'},
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {'message': 'Already enrolled in this course'},
                status=status.HTTP_200_OK
            )
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def unenroll(self, request, pk=None):
        """Unenroll current user from course"""
        course = self.get_object()
        user = request.user
        
        enrollment = CourseEnrollment.objects.filter(user=user, course=course).delete()
        
        return Response(
            {'message': f'Successfully unenrolled from {course.title}'},
            status=status.HTTP_204_NO_CONTENT
        )


# ============================================================================
# CHAPTER VIEWSET
# ============================================================================

class ChapterViewSet(viewsets.ModelViewSet):
    """
    Chapter management for a course
    
    POST /api/chapters/ - Create chapter (instructor only)
    GET /api/chapters/ - List chapters
    GET /api/chapters/{id}/ - Get chapter details
    PUT /api/chapters/{id}/ - Update chapter (instructor only)
    DELETE /api/chapters/{id}/ - Delete chapter (instructor only)
    """
    
    queryset = Chapter.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ChapterCreateSerializer
        return ChapterSerializer
    
    def create(self, request, *args, **kwargs):
        """Create chapter (instructor only)"""
        if request.user.user_type != 'instructor':
            return Response(
                {'error': 'Only instructors can create chapters'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Ensure course_id is provided
        if 'course_id' not in request.data:
            return Response(
                {'error': 'course_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Update chapter (instructor only)"""
        if request.user.user_type != 'instructor':
            return Response(
                {'error': 'Only instructors can update chapters'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Delete chapter (instructor only)"""
        if request.user.user_type != 'instructor':
            return Response(
                {'error': 'Only instructors can delete chapters'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)


# ============================================================================
# LESSON VIEWSET
# ============================================================================

class LessonViewSet(viewsets.ModelViewSet):
    """
    Lesson management for a chapter
    
    POST /api/lessons/ - Create lesson (instructor only)
    GET /api/lessons/ - List lessons
    GET /api/lessons/{id}/ - Get lesson details
    PUT /api/lessons/{id}/ - Update lesson (instructor only)
    DELETE /api/lessons/{id}/ - Delete lesson (instructor only)
    """
    
    queryset = Lesson.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return LessonCreateSerializer
        return LessonSerializer
    
    def create(self, request, *args, **kwargs):
        """Create lesson (instructor only)"""
        if request.user.user_type != 'instructor':
            return Response(
                {'error': 'Only instructors can create lessons'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Ensure chapter_id is provided
        if 'chapter_id' not in request.data:
            return Response(
                {'error': 'chapter_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Update lesson (instructor only)"""
        if request.user.user_type != 'instructor':
            return Response(
                {'error': 'Only instructors can update lessons'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Delete lesson (instructor only)"""
        if request.user.user_type != 'instructor':
            return Response(
                {'error': 'Only instructors can delete lessons'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)


# ============================================================================
# PRACTICE EXERCISE VIEWSET
# ============================================================================

class PracticeExerciseViewSet(viewsets.ModelViewSet):
    """
    Practice Exercise management for a chapter
    
    POST /api/practice-exercises/ - Create exercise (instructor only)
    GET /api/practice-exercises/ - List exercises
    GET /api/practice-exercises/{id}/ - Get exercise details
    PUT /api/practice-exercises/{id}/ - Update exercise (instructor only)
    DELETE /api/practice-exercises/{id}/ - Delete exercise (instructor only)
    """
    
    queryset = PracticeExercise.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    basename = 'practiceexercise'
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return PracticeExerciseCreateSerializer
        return PracticeExerciseSerializer
    
    def create(self, request, *args, **kwargs):
        """Create practice exercise (instructor only)"""
        if request.user.user_type != 'instructor':
            return Response(
                {'error': 'Only instructors can create practice exercises'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Ensure chapter_id is provided
        if 'chapter_id' not in request.data:
            return Response(
                {'error': 'chapter_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Update practice exercise (instructor only)"""
        if request.user.user_type != 'instructor':
            return Response(
                {'error': 'Only instructors can update practice exercises'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Delete practice exercise (instructor only)"""
        if request.user.user_type != 'instructor':
            return Response(
                {'error': 'Only instructors can delete practice exercises'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)


# ============================================================================
# QUIZ VIEWSET
# ============================================================================

class QuizViewSet(viewsets.ModelViewSet):
    """
    Quiz management for a chapter
    
    POST /api/quizzes/ - Create quiz (instructor only)
    GET /api/quizzes/ - List quizzes
    GET /api/quizzes/{id}/ - Get quiz details
    PUT /api/quizzes/{id}/ - Update quiz (instructor only)
    DELETE /api/quizzes/{id}/ - Delete quiz (instructor only)
    """
    
    queryset = Quiz.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return QuizCreateSerializer
        return QuizSerializer
    
    def create(self, request, *args, **kwargs):
        """Create quiz (instructor only)"""
        if request.user.user_type != 'instructor':
            return Response(
                {'error': 'Only instructors can create quizzes'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Ensure chapter_id is provided
        if 'chapter_id' not in request.data:
            return Response(
                {'error': 'chapter_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Update quiz (instructor only)"""
        if request.user.user_type != 'instructor':
            return Response(
                {'error': 'Only instructors can update quizzes'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Delete quiz (instructor only)"""
        if request.user.user_type != 'instructor':
            return Response(
                {'error': 'Only instructors can delete quizzes'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)
