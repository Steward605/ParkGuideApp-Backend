from django.core.management.base import BaseCommand
from courses.models import Quiz, Course
from django.db import transaction


class Command(BaseCommand):
    help = 'Fix quiz questions to have at least 3 options'

    def handle(self, *args, **options):
        """Add missing options to quiz questions that have < 3 options"""
        
        fixed_count = 0
        
        # Additional options to use for fixing questions
        additional_options = {
            'en': [
                'All of the above',
                'None of the above',
                'This varies depending on circumstances',
                'This information is not available in the material',
                'Expert discretion is required',
                'Further training is needed',
                'This depends on seasonal variations',
            ],
            'ms': [
                'Semua di atas',
                'Tiada daripada di atas',
                'Ini berbeza bergantung pada keadaan',
                'Maklumat ini tidak tersedia dalam bahan',
                'Pertimbangan pakar diperlukan',
                'Latihan lanjutan diperlukan',
                'Ini bergantung pada variasi musiman',
            ],
            'zh': [
                '以上都是',
                '以上都不是',
                '这取决于具体情况',
                '材料中没有提供此信息',
                '需要专业判断',
                '需要进一步培训',
                '这取决于季节变化',
            ],
        }
        
        with transaction.atomic():
            for course in Course.objects.all():
                for chapter in course.chapters.all():
                    for quiz in chapter.quizzes.all():
                        questions = quiz.questions
                        modified = False
                        
                        for q in questions:
                            current_options = q.get('options', [])
                            current_option_count = len(current_options)
                            
                            if current_option_count < 3:
                                # Determine how many options we need to add
                                options_to_add = 3 - current_option_count
                                
                                for i in range(options_to_add):
                                    new_option = {
                                        'text': {
                                            'en': additional_options['en'][i],
                                            'ms': additional_options['ms'][i],
                                            'zh': additional_options['zh'][i],
                                        },
                                        'is_correct': False
                                    }
                                    q['options'].append(new_option)
                                    fixed_count += 1
                                
                                self.stdout.write(
                                    self.style.SUCCESS(
                                        f"✓ {course.code} - {q.get('question_text', {}).get('en', 'Unknown')[:50]}: added {options_to_add} option(s)"
                                    )
                                )
                                modified = True
                        
                        # Save quiz if modified
                        if modified:
                            quiz.questions = questions
                            quiz.save()
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✅ Fixed {fixed_count} total quiz options!')
        )
