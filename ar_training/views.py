"""
AR Training API Views - Immersive Simulation Experience
Endpoints for 360° panoramic exploration and interactive training
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Q, F, Count
from django.utils import timezone
from datetime import datetime, timedelta

from ar_training.models import (
    ARSimulationScenario, AR360Panorama, ARInteractiveHotspot,
    ARScenarioSequence, ARSimulationQuiz, ARQuizAttempt,
    ARTrainingProgress, ARBadge, ARUserAchievement,
    ARTrainingStatistics
)
from ar_training.serializers import (
    ARScenarioListSerializer, ARScenarioDetailSerializer,
    AR360PanoramaSerializer, ARHotspotSerializer,
    ARScenarioSequenceSerializer, ARSimulationQuizSerializer,
    ARTrainingProgressSerializer, ARBadgeSerializer
)


class ARSimulationScenarioViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List and retrieve immersive AR training scenarios
    
    Query parameters:
    - type: Filter by scenario type (biodiversity, wildlife, ecotourism, conservation, guiding)
    - difficulty: Filter by difficulty (beginner, intermediate, advanced)
    - published: Filter by published status (true/false)
    """
    queryset = ARSimulationScenario.objects.filter(is_published=True).prefetch_related(
        'panoramas', 'all_hotspots', 'sequences', 'quizzes'
    ).order_by('order', '-created_at')
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ARScenarioDetailSerializer
        return ARScenarioListSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Type filter
        scenario_type = self.request.query_params.get('type')
        if scenario_type:
            queryset = queryset.filter(scenario_type=scenario_type)
        
        # Difficulty filter
        difficulty = self.request.query_params.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)
        
        return queryset
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def start(self, request, pk=None):
        """Initialize a training session for a scenario"""
        scenario = self.get_object()
        
        # Get or create progress record
        progress, created = ARTrainingProgress.objects.get_or_create(
            user=request.user,
            scenario=scenario
        )
        
        return Response({
            'scenario_id': scenario.id,
            'progress_id': progress.id,
            'panoramas_total': scenario.panoramas.count(),
            'hotspots_total': scenario.all_hotspots.count(),
            'quizzes_total': scenario.quizzes.count(),
            'sequence': ARScenarioSequenceSerializer(
                scenario.sequences.all(),
                many=True
            ).data if scenario.immersion_type == 'guided_tour' else None
        })


class AR360PanoramaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Retrieve 360° panoramic environments for AR scenarios
    """
    queryset = AR360Panorama.objects.all().prefetch_related('hotspots')
    serializer_class = AR360PanoramaSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        scenario_id = self.request.query_params.get('scenario')
        if scenario_id:
            return self.queryset.filter(scenario_id=scenario_id)
        return self.queryset
    
    @action(detail=True, methods=['get'])
    def hotspots(self, request, pk=None):
        """Get all hotspots in this panorama"""
        panorama = self.get_object()
        hotspots = panorama.hotspots.all().order_by('order')
        return Response(ARHotspotSerializer(hotspots, many=True).data)


class ARInteractiveHotspotViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Interactive learning points in panoramic views
    """
    queryset = ARInteractiveHotspot.objects.all()
    serializer_class = ARHotspotSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        panorama_id = self.request.query_params.get('panorama')
        if panorama_id:
            return self.queryset.filter(panorama_id=panorama_id).order_by('order')
        
        scenario_id = self.request.query_params.get('scenario')
        if scenario_id:
            return self.queryset.filter(scenario_id=scenario_id).order_by('order')
        
        return self.queryset
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def discover(self, request, pk=None):
        """Mark hotspot as discovered"""
        hotspot = self.get_object()
        scenario = hotspot.scenario
        
        progress, _ = ARTrainingProgress.objects.get_or_create(user=request.user, scenario=scenario)
        
        if hotspot.hotspot_id not in progress.hotspots_discovered:
            discovered = progress.hotspots_discovered
            discovered.append(hotspot.hotspot_id)
            progress.hotspots_discovered = discovered
            progress.save()
        
        return Response({
            'status': 'hotspot discovered',
            'hotspots_discovered': progress.hotspots_discovered,
            'completion_percentage': progress.completion_percentage,
        })


class ARScenarioSequenceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Tour sequence for guided AR experiences
    """
    queryset = ARScenarioSequence.objects.all()
    serializer_class = ARScenarioSequenceSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        scenario_id = self.request.query_params.get('scenario')
        if scenario_id:
            return self.queryset.filter(scenario_id=scenario_id).order_by('step_number')
        return self.queryset


class ARSimulationQuizViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Quiz questions integrated into simulations
    """
    queryset = ARSimulationQuiz.objects.all()
    serializer_class = ARSimulationQuizSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        scenario_id = self.request.query_params.get('scenario')
        if scenario_id:
            return self.queryset.filter(scenario_id=scenario_id).order_by('order')
        return self.queryset
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def answer(self, request, pk=None):
        """Submit answer to quiz question"""
        quiz = self.get_object()
        user_answer = request.data.get('answer_index')
        time_taken = request.data.get('time_taken_seconds', 0)
        
        if user_answer is None:
            return Response({'error': 'answer_index required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user_answer = int(user_answer)
        except (TypeError, ValueError):
            return Response({'error': 'answer_index must be an integer'}, status=status.HTTP_400_BAD_REQUEST)

        is_correct = user_answer == quiz.correct_option_index
        
        # Record attempt
        attempt = ARQuizAttempt.objects.create(
            user=request.user,
            quiz=quiz,
            user_answer_index=user_answer,
            is_correct=is_correct,
            time_taken_seconds=time_taken
        )
        
        # Update scenario progress
        progress, _ = ARTrainingProgress.objects.get_or_create(user=request.user, scenario=quiz.scenario)
        
        if quiz.id not in progress.quizzes_completed:
            completed = progress.quizzes_completed
            completed.append(quiz.id)
            progress.quizzes_completed = completed
            progress.save()
        
        return Response({
            'correct': is_correct,
            'correct_explanation': quiz.correct_explanation if is_correct else quiz.incorrect_explanation,
            'correct_option': quiz.correct_option_index
        })


class ARTrainingProgressViewSet(viewsets.ViewSet):
    """
    Track user progress through AR scenarios
    """
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Get user's progress on all scenarios"""
        progress = ARTrainingProgress.objects.filter(user=request.user).prefetch_related('scenario')
        return Response(ARTrainingProgressSerializer(progress, many=True).data)
    
    def retrieve(self, request, pk=None):
        """Get progress on specific scenario"""
        progress = get_object_or_404(ARTrainingProgress, id=pk, user=request.user)
        return Response(ARTrainingProgressSerializer(progress).data)
    
    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        """Update progress metrics"""
        progress = get_object_or_404(ARTrainingProgress, id=pk, user=request.user)
        
        time_added = int(request.data.get('time_spent_seconds', 0) or 0)
        progress.time_spent_seconds += max(0, time_added)

        if isinstance(request.data.get('panoramas_visited'), list):
            progress.panoramas_visited = list(dict.fromkeys(request.data['panoramas_visited']))

        if isinstance(request.data.get('hotspots_discovered'), list):
            progress.hotspots_discovered = list(dict.fromkeys(request.data['hotspots_discovered']))

        if isinstance(request.data.get('quizzes_completed'), list):
            progress.quizzes_completed = request.data['quizzes_completed']
        
        requested_completion = request.data.get('completion_percentage')
        if requested_completion is not None:
            try:
                progress.completion_percentage = max(0, min(100, float(requested_completion)))
            except (TypeError, ValueError):
                pass
        else:
            total_hotspots = progress.scenario.all_hotspots.count()
            discovered = len(progress.hotspots_discovered)
            if total_hotspots > 0:
                progress.completion_percentage = (discovered / total_hotspots) * 100
        
        if progress.completion_percentage >= 80 or request.data.get('is_completed') is True:
            progress.is_completed = True
            if not progress.completed_at:
                progress.completed_at = timezone.now()
        
        progress.save()

        stats, _ = ARTrainingStatistics.objects.get_or_create(user=request.user)
        stats.total_scenarios_attempted = ARTrainingProgress.objects.filter(user=request.user).count()
        stats.total_scenarios_completed = ARTrainingProgress.objects.filter(user=request.user, is_completed=True).count()
        stats.total_hotspots_discovered = sum(
            len(item.hotspots_discovered or [])
            for item in ARTrainingProgress.objects.filter(user=request.user)
        )
        stats.total_panoramas_visited = sum(
            len(item.panoramas_visited or [])
            for item in ARTrainingProgress.objects.filter(user=request.user)
        )
        stats.total_training_minutes = max(stats.total_training_minutes, round(
            sum(item.time_spent_seconds for item in ARTrainingProgress.objects.filter(user=request.user)) / 60
        ))
        stats.total_quiz_attempts = ARQuizAttempt.objects.filter(user=request.user).count()
        quiz_attempts = ARQuizAttempt.objects.filter(user=request.user)
        if quiz_attempts.exists():
            correct = quiz_attempts.filter(is_correct=True).count()
            stats.average_quiz_score = round((correct / quiz_attempts.count()) * 100, 1)
        stats.total_badges_earned = ARUserAchievement.objects.filter(user=request.user).count()
        stats.save()
        
        return Response(ARTrainingProgressSerializer(progress).data)


class ARBadgeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Achievement badges for training milestones
    """
    queryset = ARBadge.objects.all()
    serializer_class = ARBadgeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class ARStatisticsViewSet(viewsets.ViewSet):
    """
    User's AR training statistics and achievements
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def my_stats(self, request):
        """Get current user's AR statistics"""
        stats, created = ARTrainingStatistics.objects.get_or_create(user=request.user)
        
        # Calculate current stats
        completed = ARTrainingProgress.objects.filter(
            user=request.user,
            is_completed=True
        ).count()
        
        badges = ARUserAchievement.objects.filter(user=request.user).count()
        
        return Response({
            'scenarios_completed': completed,
            'totalScenariosCompleted': completed,
            'badges_earned': badges,
            'badgesEarned': badges,
            'total_training_minutes': stats.total_training_minutes,
            'trainingHours': round(stats.total_training_minutes / 60, 1),
            'average_quiz_score': stats.average_quiz_score,
            'averageQuizScore': stats.average_quiz_score,
            'totalHotspotsVisited': stats.total_hotspots_discovered,
            'current_streak_days': stats.current_streak_days,
            'longest_streak_days': stats.longest_streak_days
        })
    
    @action(detail=False, methods=['get'])
    def leaderboard(self, request):
        """Get top performers"""
        limit = int(request.query_params.get('limit', 10))
        
        stats = ARTrainingStatistics.objects.order_by('-total_scenarios_completed')[:limit]
        
        return Response([{
            'user': stat.user.get_full_name() or stat.user.email,
            'scenarios_completed': stat.total_scenarios_completed,
            'badges_earned': stat.total_badges_earned,
            'training_hours': stat.total_training_minutes / 60
        } for stat in stats])
