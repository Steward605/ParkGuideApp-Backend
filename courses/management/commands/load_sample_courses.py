#!/usr/bin/env python
"""
Management command to load sample training courses
"""

from django.core.management.base import BaseCommand
from courses.models import Course, Chapter, Lesson, PracticeExercise, Quiz


class Command(BaseCommand):
    help = 'Load sample training courses with chapters, lessons, practice, and quizzes'

    def handle(self, *args, **options):
        self.stdout.write('Loading sample training courses...')

        # Skip deletion, just add new courses if they don't exist
        if Course.objects.filter(code='park-orientation-101').exists():
            self.stdout.write(self.style.WARNING('Sample courses already exist. Skipping...'))

        # =====================================================================
        # COURSE 1: PARK ORIENTATION
        # =====================================================================
        course1 = Course.objects.create(
            code='park-orientation-101',
            title={'en': 'Park Orientation & Safety', 'ms': 'Orientasi & Keselamatan Taman', 'zh': '公园定向与安全'},
            description={'en': 'Learn basic park navigation and safety protocols', 'ms': 'Pelajari navigasi taman dasar dan protokol keselamatan', 'zh': '学习基本公园导航和安全协议'},
            is_published=True
        )

        # CHAPTER 1: Park Basics
        ch1_c1 = Chapter.objects.create(
            course=course1,
            title={'en': 'Park Basics', 'ms': 'Dasar Taman', 'zh': '公园基础知识'},
            description={'en': 'Introduction to park facilities and layout', 'ms': 'Pengenalan fasilitas dan tata letak taman', 'zh': '公园设施和布局介绍'},
            order=1
        )

        # Lesson 1.1
        Lesson.objects.create(
            chapter=ch1_c1,
            title={'en': 'Welcome to the Park', 'ms': 'Selamat Datang di Taman', 'zh': '欢迎来到公园'},
            content_text={'en': 'Our park spans 250 acres with diverse ecosystems. We have rainforest, wetlands, and open meadows. Each area serves a purpose in conservation...', 'ms': 'Taman kami mencakup 250 hektare dengan ekosistem yang beragam...', 'zh': '我们的公园占地250英亩，拥有多样化的生态系统...'},
            content_images=['https://example.com/park-overview.jpg'],
            content_videos=[{'url': 'https://example.com/park-intro.mp4', 'title': 'Park Overview', 'description': '5-minute tour'}],
            order=1,
            estimated_time=15
        )

        # Lesson 1.2
        Lesson.objects.create(
            chapter=ch1_c1,
            title={'en': 'Visitor Facilities', 'ms': 'Fasilitas Pengunjung', 'zh': '访客设施'},
            content_text={'en': 'Restrooms are located at all major junctions. Water stations are every 500m...', 'ms': 'Kamar kecil ditempatkan di semua persimpangan utama...', 'zh': '厕所位于所有主要枢纽...'},
            content_images=['https://example.com/facilities.jpg'],
            order=2,
            estimated_time=10
        )

        # Practice 1.1
        PracticeExercise.objects.create(
            chapter=ch1_c1,
            title={'en': 'Park Layout Quiz', 'ms': 'Kuis Tata Letak Taman', 'zh': '公园布局测验'},
            description={'en': 'Test your knowledge of park facilities', 'ms': 'Uji pengetahuan Anda tentang fasilitas taman', 'zh': '测试您对公园设施的了解'},
            exercise_type='multiple_choice',
            questions=[
                {
                    'question': 'What is the total size of the park?',
                    'options': ['150 acres', '200 acres', '250 acres', '300 acres'],
                    'correctIndex': 2,
                    'explanation': 'The park spans 250 acres as mentioned in the welcome lesson.'
                },
                {
                    'question': 'How far apart are water stations?',
                    'options': ['250m', '500m', '1000m', '1500m'],
                    'correctIndex': 1,
                    'explanation': 'Water stations are available every 500m throughout the park.'
                }
            ],
            passing_score=70,
            order=1
        )

        # Quiz 1.1
        Quiz.objects.create(
            chapter=ch1_c1,
            title={'en': 'Chapter 1 Assessment', 'ms': 'Penilaian Bab 1', 'zh': '第1章评估'},
            questions=[
                {
                    'question': 'Name two ecosystems found in the park.',
                    'options': ['Rainforest & Desert', 'Rainforest & Wetlands', 'Savanna & Wetlands', 'Desert & Tundra'],
                    'correctIndex': 1,
                    'explanation': 'The park contains rainforest, wetlands, and meadows.'
                },
                {
                    'question': 'Where should you go if you need water?',
                    'options': ['Any tree', 'Water stations', 'Visitor center', 'Gift shop'],
                    'correctIndex': 1,
                    'explanation': 'Water stations are conveniently located throughout the park.'
                }
            ],
            passing_score=70,
            time_limit=15,
            show_answers=True,
            order=1
        )

        # =====================================================================
        # COURSE 2: WILDLIFE IDENTIFICATION
        # =====================================================================
        course2 = Course.objects.create(
            code='wildlife-id-201',
            title={'en': 'Wildlife Identification', 'ms': 'Identifikasi Kehidupan Liar', 'zh': '野生动物识别'},
            description={'en': 'Learn to identify animals and birds in the park', 'ms': 'Belajar mengidentifikasi hewan dan burung di taman', 'zh': '学習如何识别公园中的动物和鸟类'},
            is_published=True
        )

        # Add prerequisite
        course2.prerequisites.add(course1)

        # CHAPTER 1: Mammals
        ch2_c1 = Chapter.objects.create(
            course=course2,
            title={'en': 'Large Mammals', 'ms': 'Mamalia Besar', 'zh': '大型哺乳动物'},
            order=1
        )

        Lesson.objects.create(
            chapter=ch2_c1,
            title={'en': 'Orangutans', 'ms': 'Orangutan', 'zh': '猩猩'},
            content_text={'en': 'Orangutans are large, arboreal primates native to Southeast Asia. They are highly intelligent...', 'ms': 'Orangutan adalah primata arboreal besar asli Asia Tenggara...', 'zh': '猩猩是原产于东南亚的大型树栖灵长类动物...'},
            content_images=['https://example.com/orangutan.jpg'],
            order=1,
            estimated_time=20
        )

        Lesson.objects.create(
            chapter=ch2_c1,
            title={'en': 'Leopards & Tigers', 'ms': 'Macan Tutul & Harimau', 'zh': '豹子和老虎'},
            content_text={'en': 'These big cats are apex predators...', 'ms': 'Kucing besar ini adalah pemangsa puncak...', 'zh': '这些大型猫科动物是顶级捕食者...'},
            order=2,
            estimated_time=18
        )

        PracticeExercise.objects.create(
            chapter=ch2_c1,
            title={'en': 'Mammal Identification', 'ms': 'Identifikasi Mamalia', 'zh': '哺乳动物识别'},
            exercise_type='multiple_choice',
            questions=[
                {
                    'question': 'What region do orangutans come from?',
                    'options': ['Africa', 'South America', 'Southeast Asia', 'Australia'],
                    'correctIndex': 2,
                    'explanation': 'Orangutans are native to Southeast Asia.'
                },
                {
                    'question': 'Which animal is NOT an apex predator?',
                    'options': ['Tiger', 'Leopard', 'Orangutan', 'Lion'],
                    'correctIndex': 2,
                    'explanation': 'Orangutans are omnivorous, not apex predators.'
                }
            ],
            passing_score=70,
            order=1
        )

        Quiz.objects.create(
            chapter=ch2_c1,
            title={'en': 'Mammal Mastery Quiz', 'ms': 'Kuis Penguasaan Mamalia', 'zh': '哺乳动物掌握测验'},
            questions=[
                {
                    'question': 'Describe the diet of orangutans.',
                    'options': ['Carnivore', 'Herbivore', 'Omnivore', 'Insectivore'],
                    'correctIndex': 2,
                    'explanation': 'Orangutans are omnivorous, eating fruits, leaves, and insects.'
                },
                {
                    'question': 'How high can orangutans climb?',
                    'options': ['10 meters', '30 meters', '50 meters', '100 meters'],
                    'correctIndex': 1,
                    'explanation': 'Orangutans can climb up to 30+ meters in tall rainforest trees.'
                }
            ],
            passing_score=70,
            time_limit=20,
            show_answers=True,
            order=1
        )

        # =====================================================================
        # COURSE 3: TOUR GUIDING EXCELLENCE
        # =====================================================================
        course3 = Course.objects.create(
            code='tour-guide-301',
            title={'en': 'Guide Techniques', 'ms': 'Teknik Memandu', 'zh': '指南技术'},
            description={'en': 'Master the art of leading engaging park tours', 'ms': 'Kuasai seni memimpin tur taman yang menarik', 'zh': '掌握领导有趣公园旅游的艺术'},
            is_published=True
        )

        ch3_c1 = Chapter.objects.create(
            course=course3,
            title={'en': 'Communication Skills', 'ms': 'Keterampilan Komunikasi', 'zh': '沟通技巧'},
            order=1
        )

        Lesson.objects.create(
            chapter=ch3_c1,
            title={'en': 'Speaking Techniques', 'ms': 'Teknik Berbicara', 'zh': '演讲技巧'},
            content_text={'en': 'Effective guiding starts with clear communication. Use simple language, avoid jargon...', 'ms': 'Panduan yang efektif dimulai dengan komunikasi yang jelas...', 'zh': '有效的指导从清晰的沟通开始...'},
            order=1,
            estimated_time=25
        )

        PracticeExercise.objects.create(
            chapter=ch3_c1,
            title={'en': 'Communication Practice', 'ms': 'Latihan Komunikasi', 'zh': '沟通练习'},
            exercise_type='scenario',
            questions=[
                {
                    'question': 'A tour guest asks a technical question you dont know. What do you do?',
                    'options': ['Make up an answer', 'Say "I dont know"', 'Offer to find out and follow up', 'Change the topic'],
                    'correctIndex': 2,
                    'explanation': 'Offering to find accurate information maintains credibility.'
                }
            ],
            passing_score=70,
            order=1
        )

        Quiz.objects.create(
            chapter=ch3_c1,
            title={'en': 'Guiding Assessment', 'ms': 'Penilaian Pemandu', 'zh': '指南评估'},
            questions=[
                {
                    'question': 'What is the most important for guest satisfaction?',
                    'options': ['How much you know', 'How you communicate', 'How fast you walk', 'Your appearance'],
                    'correctIndex': 1,
                    'explanation': 'Clear, engaging communication is key to great guiding.'
                }
            ],
            passing_score=70,
            time_limit=15,
            show_answers=True,
            order=1
        )

        self.stdout.write(self.style.SUCCESS('✓ Sample courses loaded successfully!'))
        self.stdout.write(f'  - {Course.objects.count()} courses created')
        self.stdout.write(f'  - {Chapter.objects.count()} chapters created')
        self.stdout.write(f'  - {Lesson.objects.count()} lessons created')
        self.stdout.write(f'  - {PracticeExercise.objects.count()} practice exercises created')
        self.stdout.write(f'  - {Quiz.objects.count()} quizzes created')
