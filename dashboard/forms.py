from django import forms
from courses.models import Course, Chapter, Lesson, Quiz, PracticeExercise
import json


class CourseForm(forms.ModelForm):
    """Form for creating/editing courses with multi-language support"""
    # English fields (required)
    title_en = forms.CharField(
        label="Course Name (English) *",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Park Guide Fundamentals'
        })
    )
    description_en = forms.CharField(
        label="Description (English)",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
        })
    )
    
    # Malay fields (optional)
    title_ms = forms.CharField(
        label="Course Name (Malay)",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Asas Panduan Taman'
        })
    )
    description_ms = forms.CharField(
        label="Description (Malay)",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
        })
    )
    
    # Chinese fields (optional)
    title_zh = forms.CharField(
        label="Course Name (Chinese)",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., 公园指南基础'
        })
    )
    description_zh = forms.CharField(
        label="Description (Chinese)",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
        })
    )
    
    prerequisites_list = forms.ModelMultipleChoiceField(
        queryset=Course.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Prerequisites"
    )
    
    class Meta:
        model = Course
        fields = ['code', 'thumbnail', 'is_published']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., PARK-GUIDE-101'
            }),
            'thumbnail': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com/image.jpg'
            }),
            'is_published': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['title_en'].initial = self.instance.title.get('en', '') if isinstance(self.instance.title, dict) else ''
            self.fields['title_ms'].initial = self.instance.title.get('ms', '') if isinstance(self.instance.title, dict) else ''
            self.fields['title_zh'].initial = self.instance.title.get('zh', '') if isinstance(self.instance.title, dict) else ''
            self.fields['description_en'].initial = self.instance.description.get('en', '') if isinstance(self.instance.description, dict) else ''
            self.fields['description_ms'].initial = self.instance.description.get('ms', '') if isinstance(self.instance.description, dict) else ''
            self.fields['description_zh'].initial = self.instance.description.get('zh', '') if isinstance(self.instance.description, dict) else ''
            self.fields['prerequisites_list'].initial = self.instance.prerequisites.all()
    
    def save(self, commit=True):
        course = super().save(commit=False)
        # Set multilingual fields
        course.title = {
            'en': self.cleaned_data.get('title_en'),
            'ms': self.cleaned_data.get('title_ms') or self.cleaned_data.get('title_en'),
            'zh': self.cleaned_data.get('title_zh') or self.cleaned_data.get('title_en'),
        }
        course.description = {
            'en': self.cleaned_data.get('description_en', ''),
            'ms': self.cleaned_data.get('description_ms') or self.cleaned_data.get('description_en', ''),
            'zh': self.cleaned_data.get('description_zh') or self.cleaned_data.get('description_en', ''),
        }
        if commit:
            course.save()
            course.prerequisites.set(self.cleaned_data.get('prerequisites_list', []))
        return course


class CourseImportForm(forms.Form):
    """Form for importing courses from JSON"""
    json_file = forms.FileField(
        label='JSON File',
        help_text='Upload a JSON file containing course data',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.json'
        })
    )
    
    json_text = forms.CharField(
        label='Or paste JSON directly',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 10,
            'placeholder': 'Paste JSON course data here (optional alternative to file upload)'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        json_file = cleaned_data.get('json_file')
        json_text = cleaned_data.get('json_text')
        
        # Either file or text must be provided
        if not json_file and not json_text:
            raise forms.ValidationError("Please provide either a JSON file or paste JSON text.")
        
        # Try to parse the JSON
        try:
            if json_file:
                content = json_file.read().decode('utf-8')
            else:
                content = json_text
            
            json.loads(content)
        except json.JSONDecodeError as e:
            raise forms.ValidationError(f"Invalid JSON format: {str(e)}")
        except UnicodeDecodeError:
            raise forms.ValidationError("File must be valid UTF-8 encoded JSON")
        
        return cleaned_data


class ChapterForm(forms.ModelForm):
    """Form for creating/editing chapters"""
    title_en = forms.CharField(
        label="Chapter Title (English)",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Chapter title'
        })
    )
    description_en = forms.CharField(
        label="Description (English)",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
        })
    )
    
    class Meta:
        model = Chapter
        fields = ['order']
        widgets = {
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Display order'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['title_en'].initial = self.instance.title.get('en', '')
            desc = self.instance.description or {}
            if isinstance(desc, dict):
                self.fields['description_en'].initial = desc.get('en', '')
    
    def save(self, commit=True):
        chapter = super().save(commit=False)
        chapter.title = {
            'en': self.cleaned_data.get('title_en'),
            'ms': self.cleaned_data.get('title_en'),
            'zh': self.cleaned_data.get('title_en'),
        }
        chapter.description = {
            'en': self.cleaned_data.get('description_en'),
            'ms': self.cleaned_data.get('description_en'),
            'zh': self.cleaned_data.get('description_en'),
        }
        if commit:
            chapter.save()
        return chapter


class LessonForm(forms.ModelForm):
    """Form for creating/editing lessons"""
    title_en = forms.CharField(
        label="Lesson Title (English)",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Lesson title'
        })
    )
    content_en = forms.CharField(
        label="Content (English)",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 6,
            'placeholder': 'Lesson content'
        })
    )
    
    class Meta:
        model = Lesson
        fields = ['order', 'estimated_time']
        widgets = {
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Display order'
            }),
            'estimated_time': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Estimated time in minutes'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['title_en'].initial = self.instance.title.get('en', '')
            content = self.instance.content_text or {}
            if isinstance(content, dict):
                self.fields['content_en'].initial = content.get('en', '')
    
    def save(self, commit=True):
        lesson = super().save(commit=False)
        lesson.title = {
            'en': self.cleaned_data.get('title_en'),
            'ms': self.cleaned_data.get('title_en'),
            'zh': self.cleaned_data.get('title_en'),
        }
        lesson.content_text = {
            'en': self.cleaned_data.get('content_en'),
            'ms': self.cleaned_data.get('content_en'),
            'zh': self.cleaned_data.get('content_en'),
        }
        if commit:
            lesson.save()
        return lesson


class QuizForm(forms.ModelForm):
    """Form for creating/editing quizzes"""
    title_en = forms.CharField(
        label="Quiz Title (English)",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Quiz title'
        })
    )
    description_en = forms.CharField(
        label="Description (English)",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
        })
    )
    
    class Meta:
        model = Quiz
        fields = ['order', 'passing_score', 'time_limit', 'show_answers']
        widgets = {
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Display order'
            }),
            'passing_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Passing score (%)'
            }),
            'time_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Time limit in minutes (0 = no limit)'
            }),
            'show_answers': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['title_en'].initial = self.instance.title.get('en', '')
            desc = self.instance.description or {}
            if isinstance(desc, dict):
                self.fields['description_en'].initial = desc.get('en', '')
    
    def save(self, commit=True):
        quiz = super().save(commit=False)
        quiz.title = {
            'en': self.cleaned_data.get('title_en'),
            'ms': self.cleaned_data.get('title_en'),
            'zh': self.cleaned_data.get('title_en'),
        }
        quiz.description = {
            'en': self.cleaned_data.get('description_en'),
            'ms': self.cleaned_data.get('description_en'),
            'zh': self.cleaned_data.get('description_en'),
        }
        if commit:
            quiz.save()
        return quiz


class PracticeExerciseForm(forms.ModelForm):
    """Form for creating/editing practice exercises"""
    title_en = forms.CharField(
        label="Exercise Title (English)",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Exercise title'
        })
    )
    description_en = forms.CharField(
        label="Description (English)",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
        })
    )
    
    class Meta:
        model = PracticeExercise
        fields = ['order', 'exercise_type', 'passing_score']
        widgets = {
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Display order'
            }),
            'exercise_type': forms.Select(attrs={
                'class': 'form-select',
            }),
            'passing_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Passing score (%)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['title_en'].initial = self.instance.title.get('en', '')
            desc = self.instance.description or {}
            if isinstance(desc, dict):
                self.fields['description_en'].initial = desc.get('en', '')
    
    def save(self, commit=True):
        exercise = super().save(commit=False)
        exercise.title = {
            'en': self.cleaned_data.get('title_en'),
            'ms': self.cleaned_data.get('title_en'),
            'zh': self.cleaned_data.get('title_en'),
        }
        exercise.description = {
            'en': self.cleaned_data.get('description_en'),
            'ms': self.cleaned_data.get('description_en'),
            'zh': self.cleaned_data.get('description_en'),
        }
        if commit:
            exercise.save()
        return exercise
