from django.contrib import admin
from django.db.models import Count, Q, Sum
from django.utils.html import format_html
from django import forms

from courses.models import CourseProgress, ModuleProgress
from park_guide.admin_mixins import DashboardStatsChangeListMixin

from .models import Course, Module, Chapter, Lesson, Quiz, PracticeExercise


class ModuleInline(admin.TabularInline):
    model = Module
    extra = 0
    fields = ('title', 'content', 'quiz')
    readonly_fields = ()
    show_change_link = True


@admin.register(Course)
class CourseAdmin(DashboardStatsChangeListMixin, admin.ModelAdmin):
    list_display = ('id', 'title_en', 'module_count', 'learner_coverage', 'completion_snapshot')
    search_fields = ('title',)
    inlines = [ModuleInline]
    dashboard_title = 'Training Catalogue'
    dashboard_description = 'See which courses are richest in content and how far learners are getting through them.'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            module_count_annotated=Count('modules', distinct=True),
            learner_total=Count('courseprogress', distinct=True),
            completed_total=Count('courseprogress', filter=Q(courseprogress__completed=True), distinct=True),
        )

    def title_en(self, obj):
        return obj.title.get('en', 'Untitled')
    title_en.short_description = "Title"

    def module_count(self, obj):
        return getattr(obj, 'module_count_annotated', 0)
    module_count.short_description = 'Modules'

    def learner_coverage(self, obj):
        learners = getattr(obj, 'learner_total', 0)
        return format_html('<strong>{}</strong><br><span class="admin-subtle">learners enrolled</span>', learners)
    learner_coverage.short_description = 'Learners'

    def completion_snapshot(self, obj):
        total = getattr(obj, 'learner_total', None)
        completed = getattr(obj, 'completed_total', None)
        if total is None or completed is None:
            records = CourseProgress.objects.filter(course=obj)
            total = records.count()
            completed = records.filter(completed=True).count()
        percent = 0 if total == 0 else (completed / total) * 100
        return self.render_progress_bar(percent, f'{completed}/{total} completed', tone='green')
    completion_snapshot.short_description = 'Completion'

    def get_dashboard_stats(self, request, queryset):
        module_total = queryset.aggregate(total=Sum('module_count_annotated'))['total'] or 0
        learners = CourseProgress.objects.filter(course__in=queryset).count()
        completions = CourseProgress.objects.filter(course__in=queryset, completed=True).count()
        percent = 0 if learners == 0 else round((completions / learners) * 100)
        return [
            {'label': 'Courses', 'value': queryset.count()},
            {'label': 'Modules in view', 'value': module_total},
            {'label': 'Learner records', 'value': learners},
            {'label': 'Completed courses', 'value': completions},
            {'label': 'Completion rate', 'value': f'{percent}%'},
        ]


@admin.register(Module)
class ModuleAdmin(DashboardStatsChangeListMixin, admin.ModelAdmin):
    list_display = ('id', 'course', 'title_en', 'has_quiz', 'completion_snapshot')
    list_filter = ('course',)
    search_fields = ('title',)
    dashboard_title = 'Modules'
    dashboard_description = 'Review learning units, quiz coverage, and completion health at module level.'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            learner_total=Count('moduleprogress', distinct=True),
            completed_total=Count('moduleprogress', filter=Q(moduleprogress__completed=True), distinct=True),
        )

    def title_en(self, obj):
        return obj.title.get('en', 'Untitled')
    title_en.short_description = "Title"

    def has_quiz(self, obj):
        return bool(obj.quiz)
    has_quiz.boolean = True
    has_quiz.short_description = 'Quiz'

    def completion_snapshot(self, obj):
        total = getattr(obj, 'learner_total', None)
        completed = getattr(obj, 'completed_total', None)
        if total is None or completed is None:
            records = ModuleProgress.objects.filter(module=obj)
            total = records.count()
            completed = records.filter(completed=True).count()
        percent = 0 if total == 0 else (completed / total) * 100
        return self.render_progress_bar(percent, f'{completed}/{total} complete', tone='blue')
    completion_snapshot.short_description = 'Completion'

    def get_dashboard_stats(self, request, queryset):
        with_quiz = queryset.exclude(quiz__isnull=True).exclude(quiz={}).count()
        total = queryset.count()
        module_records = ModuleProgress.objects.filter(module__in=queryset)
        module_completions = module_records.filter(completed=True).count()
        return [
            {'label': 'Modules', 'value': total},
            {'label': 'With quiz', 'value': with_quiz},
            {'label': 'Without quiz', 'value': total - with_quiz},
            {'label': 'Completions', 'value': module_completions},
        ]


# ============================================================================
# NEW COURSE SYSTEM ADMIN (Multi-language support)
# ============================================================================

class MultiLanguageForm(forms.ModelForm):
    """Base form with multi-language field support"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        
        # Process title field
        if instance and instance.title:
            self.fields['title_en'] = forms.CharField(
                label='Title (English)',
                initial=instance.title.get('en', ''),
                required=True,
                widget=forms.TextInput(attrs={'size': 50})
            )
            self.fields['title_ms'] = forms.CharField(
                label='Title (Malay)',
                initial=instance.title.get('ms', ''),
                required=False,
                widget=forms.TextInput(attrs={'size': 50}),
                help_text='Tajuk (Bahasa Malaysia)'
            )
            self.fields['title_zh'] = forms.CharField(
                label='Title (Chinese)',
                initial=instance.title.get('zh', ''),
                required=False,
                widget=forms.TextInput(attrs={'size': 50}),
                help_text='标题（中文）'
            )
        else:
            self.fields['title_en'] = forms.CharField(
                label='Title (English)',
                required=True,
                widget=forms.TextInput(attrs={'size': 50})
            )
            self.fields['title_ms'] = forms.CharField(
                label='Title (Malay)',
                required=False,
                widget=forms.TextInput(attrs={'size': 50}),
                help_text='Tajuk (Bahasa Malaysia)'
            )
            self.fields['title_zh'] = forms.CharField(
                label='Title (Chinese)',
                required=False,
                widget=forms.TextInput(attrs={'size': 50}),
                help_text='标题（中文）'
            )


class CourseNewSystemForm(MultiLanguageForm):
    """Form for the new Course system with multi-language support"""
    description_en = forms.CharField(
        label='Description (English)',
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'cols': 50})
    )
    description_ms = forms.CharField(
        label='Description (Malay)',
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'cols': 50}),
        help_text='Penerangan (Bahasa Malaysia)'
    )
    description_zh = forms.CharField(
        label='Description (Chinese)',
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'cols': 50}),
        help_text='描述（中文）'
    )
    
    class Meta:
        model = Course
        fields = ['code', 'title', 'description', 'thumbnail', 'is_published', 'prerequisites']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        
        if instance and instance.description:
            self.fields['description_en'].initial = instance.description.get('en', '')
            self.fields['description_ms'].initial = instance.description.get('ms', '')
            self.fields['description_zh'].initial = instance.description.get('zh', '')
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.title = {
            'en': self.cleaned_data.get('title_en', ''),
            'ms': self.cleaned_data.get('title_ms', ''),
            'zh': self.cleaned_data.get('title_zh', ''),
        }
        instance.description = {
            'en': self.cleaned_data.get('description_en', ''),
            'ms': self.cleaned_data.get('description_ms', ''),
            'zh': self.cleaned_data.get('description_zh', ''),
        }
        if commit:
            instance.save()
        return instance


class ChapterForm(MultiLanguageForm):
    """Form for Chapters with multi-language support"""
    description_en = forms.CharField(
        label='Description (English)',
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'cols': 50})
    )
    description_ms = forms.CharField(
        label='Description (Malay)',
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'cols': 50}),
        help_text='Penerangan (Bahasa Malaysia)'
    )
    description_zh = forms.CharField(
        label='Description (Chinese)',
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'cols': 50}),
        help_text='描述（中文）'
    )
    
    class Meta:
        model = Chapter
        fields = ['course', 'title', 'description', 'order']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        
        if instance and instance.description:
            self.fields['description_en'].initial = instance.description.get('en', '')
            self.fields['description_ms'].initial = instance.description.get('ms', '')
            self.fields['description_zh'].initial = instance.description.get('zh', '')
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.title = {
            'en': self.cleaned_data.get('title_en', ''),
            'ms': self.cleaned_data.get('title_ms', ''),
            'zh': self.cleaned_data.get('title_zh', ''),
        }
        instance.description = {
            'en': self.cleaned_data.get('description_en', ''),
            'ms': self.cleaned_data.get('description_ms', ''),
            'zh': self.cleaned_data.get('description_zh', ''),
        }
        if commit:
            instance.save()
        return instance


class LessonForm(MultiLanguageForm):
    """Form for Lessons with multi-language support"""
    content_text_en = forms.CharField(
        label='Content (English)',
        required=False,
        widget=forms.Textarea(attrs={'rows': 8, 'cols': 50}),
        help_text='Markdown or HTML content'
    )
    content_text_ms = forms.CharField(
        label='Content (Malay)',
        required=False,
        widget=forms.Textarea(attrs={'rows': 8, 'cols': 50}),
        help_text='Kandungan (Bahasa Malaysia) - Markdown atau HTML'
    )
    content_text_zh = forms.CharField(
        label='Content (Chinese)',
        required=False,
        widget=forms.Textarea(attrs={'rows': 8, 'cols': 50}),
        help_text='内容（中文）- Markdown或HTML'
    )
    
    class Meta:
        model = Lesson
        fields = ['chapter', 'title', 'content_text', 'content_images', 'content_videos', 'order', 'estimated_time']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        
        if instance and instance.content_text:
            self.fields['content_text_en'].initial = instance.content_text.get('en', '')
            self.fields['content_text_ms'].initial = instance.content_text.get('ms', '')
            self.fields['content_text_zh'].initial = instance.content_text.get('zh', '')
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.title = {
            'en': self.cleaned_data.get('title_en', ''),
            'ms': self.cleaned_data.get('title_ms', ''),
            'zh': self.cleaned_data.get('title_zh', ''),
        }
        instance.content_text = {
            'en': self.cleaned_data.get('content_text_en', ''),
            'ms': self.cleaned_data.get('content_text_ms', ''),
            'zh': self.cleaned_data.get('content_text_zh', ''),
        }
        if commit:
            instance.save()
        return instance


class QuizForm(MultiLanguageForm):
    """Form for Quizzes with multi-language support"""
    description_en = forms.CharField(
        label='Description (English)',
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'cols': 50})
    )
    description_ms = forms.CharField(
        label='Description (Malay)',
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'cols': 50}),
        help_text='Penerangan (Bahasa Malaysia)'
    )
    description_zh = forms.CharField(
        label='Description (Chinese)',
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'cols': 50}),
        help_text='描述（中文）'
    )
    
    class Meta:
        model = Quiz
        fields = ['chapter', 'title', 'description', 'questions', 'passing_score', 'time_limit', 'show_answers', 'order']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        
        if instance and instance.description:
            self.fields['description_en'].initial = instance.description.get('en', '')
            self.fields['description_ms'].initial = instance.description.get('ms', '')
            self.fields['description_zh'].initial = instance.description.get('zh', '')
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.title = {
            'en': self.cleaned_data.get('title_en', ''),
            'ms': self.cleaned_data.get('title_ms', ''),
            'zh': self.cleaned_data.get('title_zh', ''),
        }
        instance.description = {
            'en': self.cleaned_data.get('description_en', ''),
            'ms': self.cleaned_data.get('description_ms', ''),
            'zh': self.cleaned_data.get('description_zh', ''),
        }
        if commit:
            instance.save()
        return instance


class PracticeExerciseForm(MultiLanguageForm):
    """Form for Practice Exercises with multi-language support"""
    description_en = forms.CharField(
        label='Description (English)',
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'cols': 50})
    )
    description_ms = forms.CharField(
        label='Description (Malay)',
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'cols': 50}),
        help_text='Penerangan (Bahasa Malaysia)'
    )
    description_zh = forms.CharField(
        label='Description (Chinese)',
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'cols': 50}),
        help_text='描述（中文）'
    )
    
    class Meta:
        model = PracticeExercise
        fields = ['chapter', 'title', 'description', 'exercise_type', 'questions', 'passing_score', 'order']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        
        if instance and instance.description:
            self.fields['description_en'].initial = instance.description.get('en', '')
            self.fields['description_ms'].initial = instance.description.get('ms', '')
            self.fields['description_zh'].initial = instance.description.get('zh', '')
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.title = {
            'en': self.cleaned_data.get('title_en', ''),
            'ms': self.cleaned_data.get('title_ms', ''),
            'zh': self.cleaned_data.get('title_zh', ''),
        }
        instance.description = {
            'en': self.cleaned_data.get('description_en', ''),
            'ms': self.cleaned_data.get('description_ms', ''),
            'zh': self.cleaned_data.get('description_zh', ''),
        }
        if commit:
            instance.save()
        return instance


# ============================================================================
# ADMIN REGISTRATIONS
# ============================================================================

@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    form = ChapterForm
    list_display = ('id', 'course', 'title_en', 'order')
    list_filter = ('course',)
    search_fields = ('title',)
    ordering = ('course', 'order')
    
    def title_en(self, obj):
        return obj.title.get('en', 'Untitled')
    title_en.short_description = 'Title'


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    form = LessonForm
    list_display = ('id', 'chapter', 'title_en', 'order', 'estimated_time')
    list_filter = ('chapter__course', 'chapter')
    search_fields = ('title',)
    ordering = ('chapter', 'order')
    
    def title_en(self, obj):
        return obj.title.get('en', 'Untitled')
    title_en.short_description = 'Title'


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    form = QuizForm
    list_display = ('id', 'chapter', 'title_en', 'passing_score', 'time_limit')
    list_filter = ('chapter__course', 'chapter')
    search_fields = ('title',)
    
    def title_en(self, obj):
        return obj.title.get('en', 'Untitled')
    title_en.short_description = 'Title'


@admin.register(PracticeExercise)
class PracticeExerciseAdmin(admin.ModelAdmin):
    form = PracticeExerciseForm
    list_display = ('id', 'chapter', 'title_en', 'exercise_type', 'passing_score', 'order')
    list_filter = ('chapter__course', 'chapter', 'exercise_type')
    search_fields = ('title',)
    ordering = ('chapter', 'order')
    
    def title_en(self, obj):
        return obj.title.get('en', 'Untitled')
    title_en.short_description = 'Title'
