from django.core.management.base import BaseCommand
from courses.models import Course, Chapter, Lesson, PracticeExercise, Quiz
from django.utils import timezone


class Command(BaseCommand):
    help = 'Load sample course data compatible with the new Canvas-like LMS system'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Starting to load sample data...'))
        
        # Clear existing data
        self.stdout.write('Clearing existing courses...')
        Course.objects.all().delete()
        
        # Define sample courses
        courses_data = [
            {
                'code': 'park-guide-101',
                'title': {
                    'en': 'Park Guide Fundamentals',
                    'ms': 'Asas Panduan Taman',
                    'zh': '公园导游基础'
                },
                'description': {
                    'en': 'Learn the essential skills and responsibilities of a professional park guide, including visitor safety and park orientation.',
                    'ms': 'Pelajari kemahiran dan tanggung jawab penting seorang panduan taman profesional, termasuk keselamatan pengunjung dan orientasi taman.',
                    'zh': '学习专业公园导游的基本技能和职责，包括游客安全和公园导览。'
                },
                'thumbnail': 'https://images.unsplash.com/photo-1488749807830-63789f68bb65?w=400',
                'chapters': [
                    {
                        'title': {
                            'en': 'Park Orientation & Safety',
                            'ms': 'Orientasi Taman & Keselamatan',
                            'zh': '公园导览与安全'
                        },
                        'lessons': [
                            {
                                'title': {
                                    'en': 'Introduction to Bako National Park',
                                    'ms': 'Pengenalan ke Taman Negara Bako',
                                    'zh': '巴哥国家公园简介'
                                },
                                'content_text': {
                                    'en': 'Bako National Park is one of Sarawak\'s oldest national parks, established in 1957. It covers an area of 2,727 hectares and is home to diverse ecosystems and wildlife. As a guide, you must be familiar with the park\'s geography, visitor routes, and emergency procedures.',
                                    'ms': 'Taman Negara Bako adalah salah satu taman negara tertua Sarawak, ditubuhkan pada tahun 1957. Ia meliputi kawasan seluas 2,727 hektar dan adalah rumah kepada ekosistem dan hidupan liar yang pelbagai. Sebagai panduan, anda mesti akrab dengan geografi taman, laluan pelawat, dan prosedur kecemasan.',
                                    'zh': '巴哥国家公园是砂州最古老的国家公园之一，成立于1957年。它的面积为2,727公顷，是各种生态系统和野生动物的家园。作为导游，您必须熟悉公园的地理、游客路线和应急程序。'
                                },
                                'content_images': ['https://images.unsplash.com/photo-1488749807830-63789f68bb65?w=500'],
                                'content_videos': [
                                    {
                                        'url': 'https://www.youtube.com/embed/dQw4w9WgXcQ',
                                        'title': 'Park Overview',
                                        'description': 'Introduction to Bako National Park'
                                    }
                                ],
                            },
                            {
                                'title': {
                                    'en': 'Emergency Procedures',
                                    'ms': 'Prosedur Kecemasan',
                                    'zh': '应急程序'
                                },
                                'content_text': {
                                    'en': 'Every guide must know the emergency procedures including evacuation routes, first aid basics, and how to contact emergency services. Visitor safety is your primary responsibility.',
                                    'ms': 'Setiap panduan mesti tahu prosedur kecemasan termasuk laluan evakuasi, asas pertolongan pertama, dan cara menghubungi perkhidmatan kecemasan. Keselamatan pengunjung adalah tanggung jawab utama anda.',
                                    'zh': '每位导游必须了解应急程序，包括撤离路线、急救基础知识以及如何联系紧急服务。游客安全是您的主要职责。'
                                },
                                'content_images': [],
                                'content_videos': [],
                            },
                        ],
                        'practice_exercises': [
                            {
                                'title': {
                                    'en': 'Park Safety Scenario',
                                    'ms': 'Senario Keselamatan Taman',
                                    'zh': '公园安全情景'
                                },
                                'exercise_type': 'scenario',
                                'questions': [
                                    {
                                        'question_text': {
                                            'en': 'A visitor twists their ankle on the trail. What is your first action?',
                                            'ms': 'Seorang pelawat terseliuh pada jejak. Apakah tindakan pertama anda?',
                                            'zh': '一位游客在步道上扭伤了脚踝。您的第一个行动是什么？'
                                        },
                                        'question_type': 'multiple_choice',
                                        'options': [
                                            {
                                                'text': {
                                                    'en': 'Assess the injury and provide first aid',
                                                    'ms': 'Nilai kecederaan dan berikan pertolongan pertama',
                                                    'zh': '评估伤情并提供急救'
                                                },
                                                'is_correct': True
                                            },
                                            {
                                                'text': {
                                                    'en': 'Continue the tour',
                                                    'ms': 'Teruskan lawatan',
                                                    'zh': '继续旅游'
                                                },
                                                'is_correct': False
                                            },
                                            {
                                                'text': {
                                                    'en': 'Ask them to walk it off',
                                                    'ms': 'Minta mereka berjalan',
                                                    'zh': '让他们自己走动'
                                                },
                                                'is_correct': False
                                            },
                                        ]
                                    }
                                ]
                            }
                        ],
                        'quizzes': [
                            {
                                'title': {
                                    'en': 'Park Orientation Quiz',
                                    'ms': 'Kuis Orientasi Taman',
                                    'zh': '公园导览测验'
                                },
                                'time_limit': 15,
                                'questions': [
                                    {
                                        'question_text': {
                                            'en': 'When was Bako National Park established?',
                                            'ms': 'Bilakah Taman Negara Bako ditubuhkan?',
                                            'zh': '巴哥国家公园是何时成立的？'
                                        },
                                        'question_type': 'multiple_choice',
                                        'options': [
                                            {
                                                'text': {'en': '1957', 'ms': '1957', 'zh': '1957'},
                                                'is_correct': True
                                            },
                                            {
                                                'text': {'en': '1965', 'ms': '1965', 'zh': '1965'},
                                                'is_correct': False
                                            },
                                            {
                                                'text': {'en': '1975', 'ms': '1975', 'zh': '1975'},
                                                'is_correct': False
                                            },
                                        ]
                                    },
                                    {
                                        'question_text': {
                                            'en': 'What is the total area of Bako National Park?',
                                            'ms': 'Berapa jumlah keluasan Taman Negara Bako?',
                                            'zh': '巴哥国家公园的总面积是多少？'
                                        },
                                        'question_type': 'multiple_choice',
                                        'options': [
                                            {
                                                'text': {'en': '2,727 hectares', 'ms': '2,727 hektar', 'zh': '2,727公顷'},
                                                'is_correct': True
                                            },
                                            {
                                                'text': {'en': '1,500 hectares', 'ms': '1,500 hektar', 'zh': '1,500公顷'},
                                                'is_correct': False
                                            },
                                        ]
                                    },
                                ]
                            }
                        ]
                    },
                    {
                        'title': {
                            'en': 'Wildlife & Ecology',
                            'ms': 'Hidupan Liar & Ekologi',
                            'zh': '野生动物与生态'
                        },
                        'lessons': [
                            {
                                'title': {
                                    'en': 'Flora & Fauna of Bako',
                                    'ms': 'Flora & Fauna Bako',
                                    'zh': '巴哥的植物群和动物群'
                                },
                                'content_text': {
                                    'en': 'Bako National Park is home to proboscis monkeys, bearded pigs, and over 150 bird species. Understanding the wildlife helps you provide engaging tours and educate visitors about conservation.',
                                    'ms': 'Taman Negara Bako adalah rumah kepada monyet hidung panjang, babi janggut, dan lebih daripada 150 spesies burung. Memahami hidupan liar membantu anda memberikan lawatan yang menarik dan mendidik pelawat tentang pemuliharaan.',
                                    'zh': '巴哥国家公园是长鼻猴、胡须猪和150多种鸟类的家园。了解野生动物可帮助您提供有趣的旅游和教育游客关于保护。'
                                },
                                'content_images': ['https://images.unsplash.com/photo-1474511320723-9a56873867b5?w=500'],
                                'content_videos': [],
                            },
                        ],
                        'practice_exercises': [],
                        'quizzes': [
                            {
                                'title': {
                                    'en': 'Wildlife Knowledge Quiz',
                                    'ms': 'Kuis Pengetahuan Hidupan Liar',
                                    'zh': '野生动物知识测验'
                                },
                                'time_limit': 10,
                                'questions': [
                                    {
                                        'question_text': {
                                            'en': 'Which primate is unique to Bako National Park?',
                                            'ms': 'Apakah primata yang unik untuk Taman Negara Bako?',
                                            'zh': '哪种灵长类动物是巴哥国家公园独有的？'
                                        },
                                        'question_type': 'multiple_choice',
                                        'options': [
                                            {
                                                'text': {'en': 'Proboscis monkey', 'ms': 'Monyet hidung panjang', 'zh': '长鼻猴'},
                                                'is_correct': True
                                            },
                                            {
                                                'text': {'en': 'Orangutan', 'ms': 'Orangutan', 'zh': '猩猩'},
                                                'is_correct': False
                                            },
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            },
            {
                'code': 'park-guide-201',
                'title': {
                    'en': 'Advanced Guiding Techniques',
                    'ms': 'Teknik Panduan Lanjutan',
                    'zh': '高级导游技巧'
                },
                'description': {
                    'en': 'Master advanced interpretation, group management, and storytelling techniques to enhance visitor experiences.',
                    'ms': 'Kuasai tafsiran lanjutan, pengurusan kumpulan, dan teknik bercerita untuk meningkatkan pengalaman pelawat.',
                    'zh': '掌握高级解释、团队管理和故事讲述技巧，以增强游客体验。'
                },
                'thumbnail': 'https://images.unsplash.com/photo-1552664730-d307ca884978?w=400',
                'chapters': [
                    {
                        'title': {
                            'en': 'Interpretation Skills',
                            'ms': 'Kemahiran Tafsiran',
                            'zh': '解释技巧'
                        },
                        'lessons': [
                            {
                                'title': {
                                    'en': 'Storytelling for Engagement',
                                    'ms': 'Bercerita untuk Penglibatan',
                                    'zh': '为参与而讲故事'
                                },
                                'content_text': {
                                    'en': 'Effective guides use stories to make learning memorable. Connect flora, fauna, and park history through engaging narratives that visitors will remember long after their visit.',
                                    'ms': 'Panduan yang berkesan menggunakan cerita untuk menjadikan pembelajaran dapat diingati. Sambungkan flora, fauna, dan sejarah taman melalui narasi yang menarik yang akan pelawat ingat lama selepas lawatan mereka.',
                                    'zh': '有效的导游使用故事来让学习令人难忘。通过引人入胜的叙事连接植物群、动物群和公园历史，这些叙事在访问后很久都会被游客记住。'
                                },
                                'content_images': [],
                                'content_videos': [],
                            },
                        ],
                        'practice_exercises': [],
                        'quizzes': []
                    }
                ]
            },
        ]

        # Create courses with all related data
        for course_data in courses_data:
            self.stdout.write(f'Creating course: {course_data["title"]["en"]}')
            
            course = Course.objects.create(
                code=course_data['code'],
                title=course_data['title'],
                description=course_data['description'],
                thumbnail=course_data.get('thumbnail', ''),
                is_published=True
            )
            
            # Create chapters
            for chapter_index, chapter_data in enumerate(course_data.get('chapters', [])):
                self.stdout.write(f'  Creating chapter: {chapter_data["title"]["en"]}')
                
                chapter = Chapter.objects.create(
                    course=course,
                    title=chapter_data['title'],
                    description=chapter_data.get('description', {}),
                    order=chapter_index + 1
                )
                
                # Create lessons
                for lesson_index, lesson_data in enumerate(chapter_data.get('lessons', [])):
                    self.stdout.write(f'    Creating lesson: {lesson_data["title"]["en"]}')
                    
                    Lesson.objects.create(
                        chapter=chapter,
                        title=lesson_data['title'],
                        content_text=lesson_data.get('content_text', {}),
                        content_images=lesson_data.get('content_images', []),
                        content_videos=lesson_data.get('content_videos', []),
                        order=lesson_index + 1,
                        estimated_time=10
                    )
                
                # Create practice exercises
                for exercise_index, exercise_data in enumerate(chapter_data.get('practice_exercises', [])):
                    self.stdout.write(f'    Creating practice exercise: {exercise_data["title"]["en"]}')
                    
                    PracticeExercise.objects.create(
                        chapter=chapter,
                        title=exercise_data['title'],
                        exercise_type=exercise_data.get('exercise_type', 'multiple_choice'),
                        questions=exercise_data.get('questions', []),
                        order=exercise_index + 1
                    )
                
                # Create quizzes
                for quiz_index, quiz_data in enumerate(chapter_data.get('quizzes', [])):
                    self.stdout.write(f'    Creating quiz: {quiz_data["title"]["en"]}')
                    
                    Quiz.objects.create(
                        chapter=chapter,
                        title=quiz_data['title'],
                        time_limit=quiz_data.get('time_limit', 30),
                        questions=quiz_data.get('questions', []),
                        order=quiz_index + 1
                    )
        
        self.stdout.write(self.style.SUCCESS('✓ Sample data loaded successfully!'))
        
        # Verify
        course_count = Course.objects.count()
        chapter_count = Chapter.objects.count()
        lesson_count = Lesson.objects.count()
        exercise_count = PracticeExercise.objects.count()
        quiz_count = Quiz.objects.count()
        
        self.stdout.write(self.style.SUCCESS(f'\nData Summary:'))
        self.stdout.write(f'  Courses: {course_count}')
        self.stdout.write(f'  Chapters: {chapter_count}')
        self.stdout.write(f'  Lessons: {lesson_count}')
        self.stdout.write(f'  Practice Exercises: {exercise_count}')
        self.stdout.write(f'  Quizzes: {quiz_count}')
