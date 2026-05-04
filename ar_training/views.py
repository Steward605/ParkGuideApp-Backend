"""
AR Training Views
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Q, F
from datetime import datetime, timedelta

from ar_training.models import (
    ARScenario, AREnvironment, ARHotspot, ARQuizQuestion,
    ARTrainingProgress, ARQuizResult, ARBadge, ARUserAchievement,
    ARTrainingStatistics
)
from ar_training.serializers import (
    ARScenarioListSerializer, ARScenarioDetailSerializer,
    AREnvironmentSerializer, ARHotspotSerializer, ARQuizQuestionSerializer,
    ARTrainingProgressSerializer, ARQuizResultSerializer,
    ARBadgeSerializer, ARUserAchievementSerializer, ARTrainingStatisticsSerializer
)


class ARScenarioViewSet(viewsets.ReadOnlyModelViewSet):
    """
    AR Scenarios endpoint
    GET /api/ar-training/scenarios/ - List all published scenarios
    GET /api/ar-training/scenarios/{id}/ - Get scenario details
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        queryset = ARScenario.objects.filter(is_published=True)
        
        # Filter by type
        scenario_type = self.request.query_params.get('type')
        if scenario_type:
            queryset = queryset.filter(scenario_type=scenario_type)
        
        return queryset.prefetch_related('environments', 'hotspots', 'quiz_questions')
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ARScenarioDetailSerializer
        return ARScenarioListSerializer


class AREnvironmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    AR Environments endpoint
    GET /api/ar-training/environments/ - List all environments
    GET /api/ar-training/environments/{id}/ - Get environment details
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = AREnvironmentSerializer
    
    def get_queryset(self):
        scenario_id = self.request.query_params.get('scenario_id')
        queryset = AREnvironment.objects.all()
        
        if scenario_id:
            queryset = queryset.filter(scenario_id=scenario_id)
        
        return queryset.order_by('order')


class ARHotspotViewSet(viewsets.ReadOnlyModelViewSet):
    """
    AR Hotspots endpoint
    GET /api/ar-training/hotspots/ - List all hotspots
    GET /api/ar-training/hotspots/{id}/ - Get hotspot details
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = ARHotspotSerializer
    
    def get_queryset(self):
        scenario_id = self.request.query_params.get('scenario_id')
        queryset = ARHotspot.objects.all()
        
        if scenario_id:
            queryset = queryset.filter(scenario_id=scenario_id)
        
        return queryset.order_by('order')


class ARTrainingProgressViewSet(viewsets.ModelViewSet):
    """
    User AR Training Progress
    GET /api/ar-training/progress/ - List user's progress
    POST /api/ar-training/progress/ - Create progress record
    GET /api/ar-training/progress/{id}/ - Get progress details
    PUT /api/ar-training/progress/{id}/ - Update progress
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ARTrainingProgressSerializer
    
    def get_queryset(self):
        return ARTrainingProgress.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def perform_update(self, serializer):
        # Update completion percentage
        visited = len(serializer.validated_data.get('visited_hotspots', []))
        total_hotspots = serializer.instance.scenario.hotspots.count()
        percentage = (visited / total_hotspots * 100) if total_hotspots > 0 else 0
        
        serializer.save(
            completion_percentage=percentage,
            is_completed=(percentage >= 100)
        )
    
    @action(detail=False, methods=['get'])
    def by_scenario(self, request):
        """Get progress for specific scenario"""
        scenario_id = request.query_params.get('scenario_id')
        if not scenario_id:
            return Response({'error': 'scenario_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        progress = get_object_or_404(
            ARTrainingProgress,
            user=request.user,
            scenario_id=scenario_id
        )
        serializer = self.get_serializer(progress)
        return Response(serializer.data)


class ARQuizViewSet(viewsets.ModelViewSet):
    """
    AR Quiz Questions endpoint
    GET /api/ar-training/quiz/ - List quiz questions
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = ARQuizQuestionSerializer
    
    def get_queryset(self):
        scenario_id = self.request.query_params.get('scenario_id')
        queryset = ARQuizQuestion.objects.all()
        
        if scenario_id:
            queryset = queryset.filter(scenario_id=scenario_id)
        
        return queryset.order_by('order')


class ARQuizResultViewSet(viewsets.ModelViewSet):
    """
    AR Quiz Results endpoint
    POST /api/ar-training/quiz-results/ - Submit quiz result
    GET /api/ar-training/quiz-results/ - List user's quiz results
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ARQuizResultSerializer
    
    def get_queryset(self):
        return ARQuizResult.objects.filter(user=self.request.user)
    
    def create(self, request):
        """Submit quiz result and calculate score"""
        scenario_id = request.data.get('scenario_id')
        answers = request.data.get('answers', {})
        time_spent = request.data.get('time_spent_seconds', 0)
        
        scenario = get_object_or_404(ARScenario, id=scenario_id)
        questions = ARQuizQuestion.objects.filter(scenario=scenario).order_by('order')
        
        # Calculate score
        score = 0
        total = questions.count()
        
        for question in questions:
            user_answer = answers.get(str(question.id))
            if user_answer == question.correct_option:
                score += 1
        
        percentage = (score / total * 100) if total > 0 else 0
        passed = percentage >= 70  # Default passing score
        
        # Create result
        result = ARQuizResult.objects.create(
            user=request.user,
            scenario=scenario,
            answers=answers,
            score=score,
            total_questions=total,
            percentage=percentage,
            passed=passed,
            time_spent_seconds=time_spent
        )
        
        # Update statistics
        self._update_user_statistics(request.user, scenario)
        
        # Check for achievements
        self._check_achievements(request.user)
        
        serializer = self.get_serializer(result)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def _update_user_statistics(self, user, scenario):
        """Update user's training statistics"""
        stats, _ = ARTrainingStatistics.objects.get_or_create(user=user)
        
        # Calculate aggregates
        all_results = ARQuizResult.objects.filter(user=user)
        all_progress = ARTrainingProgress.objects.filter(user=user, is_completed=True)
        
        stats.total_scenarios_completed = all_progress.count()
        stats.total_hotspots_visited = sum(len(p.visited_hotspots) for p in all_progress)
        stats.average_quiz_score = all_results.aggregate(Avg('percentage'))['percentage__avg'] or 0
        
        # Calculate total hours
        total_seconds = sum(p.time_spent_seconds for p in all_progress) + sum(r.time_spent_seconds for r in all_results)
        stats.total_training_hours = total_seconds / 3600
        
        # Update streak
        today = datetime.now().date()
        stats.last_training_date = today
        stats.save()
    
    def _check_achievements(self, user):
        """Check and award achievements based on progress"""
        # Forest Explorer - Visit all forest hotspots
        forest_scenarios = ARScenario.objects.filter(scenario_type='forest')
        for scenario in forest_scenarios:
            progress = ARTrainingProgress.objects.filter(user=user, scenario=scenario, is_completed=True).first()
            if progress:
                badge = ARBadge.objects.filter(badge_id='forest_explorer').first()
                if badge:
                    ARUserAchievement.objects.get_or_create(user=user, badge=badge)
        
        # Quiz Master - Score 90%+
        high_scores = ARQuizResult.objects.filter(user=user, percentage__gte=90).count()
        if high_scores >= 3:
            badge = ARBadge.objects.filter(badge_id='quiz_master').first()
            if badge:
                ARUserAchievement.objects.get_or_create(user=user, badge=badge)


class ARBadgeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    AR Badges endpoint
    GET /api/ar-training/badges/ - List all available badges
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ARBadgeSerializer
    queryset = ARBadge.objects.all()


class ARUserAchievementViewSet(viewsets.ReadOnlyModelViewSet):
    """
    User Achievements endpoint
    GET /api/ar-training/achievements/ - List user's achievements
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ARUserAchievementSerializer
    
    def get_queryset(self):
        return ARUserAchievement.objects.filter(user=self.request.user)


class ARStatisticsViewSet(viewsets.ViewSet):
    """
    AR Training Statistics endpoint
    GET /api/ar-training/statistics/ - Get user statistics
    GET /api/ar-training/statistics/leaderboard/ - Get leaderboard
    """
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Get user's training statistics"""
        stats, _ = ARTrainingStatistics.objects.get_or_create(user=request.user)
        serializer = ARTrainingStatisticsSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def leaderboard(self, request):
        """Get leaderboard by scenario type"""
        scenario_type = request.query_params.get('type', 'forest')
        limit = int(request.query_params.get('limit', 10))
        
        # Get top quiz scores for scenario type
        top_users = ARQuizResult.objects.filter(
            scenario__scenario_type=scenario_type
        ).values('user__email').annotate(
            avg_score=Avg('percentage')
        ).order_by('-avg_score')[:limit]
        
        return Response(top_users)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get training summary"""
        stats, _ = ARTrainingStatistics.objects.get_or_create(user=request.user)
        serializer = ARTrainingStatisticsSerializer(stats)
        return Response(serializer.data)
