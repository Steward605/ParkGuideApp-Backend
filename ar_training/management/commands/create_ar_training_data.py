"""
Management command to create sample AR training data
Usage: python manage.py create_ar_training_data
"""
from django.core.management.base import BaseCommand
from ar_training.models import (
    ARScenario, AREnvironment, ARHotspot, ARQuizQuestion, ARBadge
)


class Command(BaseCommand):
    help = 'Create sample AR training scenarios, environments, and quiz data'
    
    def handle(self, *args, **options):
        self.stdout.write("Creating AR Training Sample Data...")
        
        # Create Scenarios
        forest_scenario = ARScenario.objects.create(
            code='ar-biodiversity-101',
            title={
                'en': 'AR Forest Biodiversity Training',
                'ms': 'Latihan AR Biodiversiti Hutan',
                'zh': 'AR森林生物多样性培训'
            },
            description={
                'en': 'Learn about forest ecosystem layers and species relationships',
                'ms': 'Pelajari tentang lapisan ekosistem hutan dan hubungan spesies',
                'zh': '了解森林生态系统层和物种关系'
            },
            scenario_type='forest',
            difficulty='intermediate',
            duration_minutes=20,
            is_published=True
        )
        
        eco_scenario = ARScenario.objects.create(
            code='ar-ecotourism-101',
            title={
                'en': 'AR Eco-tourism Practice',
                'ms': 'Amalan AR Eko-pelancongan',
                'zh': 'AR生态旅游实践'
            },
            description={
                'en': 'Train sustainable tourism and visitor management',
                'ms': 'Latih pelancongan lestari dan pengurusan pelawat',
                'zh': '培训可持续旅游和游客管理'
            },
            scenario_type='eco',
            difficulty='intermediate',
            duration_minutes=25,
            is_published=True
        )
        
        wildlife_scenario = ARScenario.objects.create(
            code='ar-wildlife-101',
            title={
                'en': 'AR Wildlife Encounter Response',
                'ms': 'Respons AR Pertemuan Hidupan Liar',
                'zh': 'AR野生动物遭遇应对'
            },
            description={
                'en': 'Learn safe wildlife encounter protocols',
                'ms': 'Pelajari protokol pertemuan hidupan liar yang selamat',
                'zh': '学习安全的野生动物遭遇协议'
            },
            scenario_type='wildlife',
            difficulty='advanced',
            duration_minutes=20,
            is_published=True
        )
        
        self.stdout.write(self.style.SUCCESS(f'Created 3 scenarios'))
        
        # Create Environments
        environments_data = [
            {
                'scenario': forest_scenario,
                'name': 'Tropical Rainforest',
                'panorama_url': 'https://images.unsplash.com/photo-1511593358241-7eea1f3c84e5?w=1200&h=800&fit=crop',
                'order': 1
            },
            {
                'scenario': forest_scenario,
                'name': 'Temperate Forest',
                'panorama_url': 'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=1200&h=800&fit=crop',
                'order': 2
            },
            {
                'scenario': eco_scenario,
                'name': 'Conservation Area',
                'panorama_url': 'https://images.unsplash.com/photo-1469022563149-aa64dbd37dae?w=1200&h=800&fit=crop',
                'order': 1
            },
            {
                'scenario': wildlife_scenario,
                'name': 'Jungle Canopy',
                'panorama_url': 'https://images.unsplash.com/photo-1505142468610-359e7d316be0?w=1200&h=800&fit=crop',
                'order': 1
            },
        ]
        
        for env_data in environments_data:
            AREnvironment.objects.create(**env_data)
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(environments_data)} environments'))
        
        # Create Hotspots
        hotspots_data = [
            {
                'scenario': forest_scenario,
                'hotspot_id': 'canopy_layer',
                'title': {'en': 'Canopy Layer', 'ms': 'Lapisan Kanopi', 'zh': '冠层'},
                'position_x': 24,
                'position_y': 23,
                'content': {
                    'species': 'Emergent Trees',
                    'scientific': 'Various tall species',
                    'height': 'Above 40m',
                    'characteristics': {
                        'en': 'These are the tallest trees emerging above canopy',
                        'ms': 'Ini adalah pokok tertinggi yang muncul di atas kanopi',
                        'zh': '这些是从冠层上方突出的最高树木'
                    }
                },
                'order': 1
            },
            {
                'scenario': forest_scenario,
                'hotspot_id': 'understory',
                'title': {'en': 'Understory Plants', 'ms': 'Tumbuhan Lapisan Bawah', 'zh': '林下植物'},
                'position_x': 63,
                'position_y': 48,
                'content': {
                    'species': 'Young Trees & Shrubs',
                    'scientific': 'Seedlings and juvenile plants',
                    'height': '2-15m',
                    'characteristics': {
                        'en': 'Shade-tolerant plants waiting to grow',
                        'ms': 'Tumbuhan tahan bayang menunggu untuk berkembang',
                        'zh': '耐阴植物等待生长'
                    }
                },
                'order': 2
            },
        ]
        
        for hotspot_data in hotspots_data:
            ARHotspot.objects.create(**hotspot_data)
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(hotspots_data)} hotspots'))
        
        # Create Quiz Questions
        quiz_data = [
            {
                'scenario': forest_scenario,
                'question_id': 'q1',
                'question_text': {
                    'en': 'What are the four main layers of a tropical forest?',
                    'ms': 'Apakah empat lapisan utama hutan tropika?',
                    'zh': '热带森林的四个主要层是什么？'
                },
                'options': {
                    'en': [
                        'Emergent, Canopy, Understory, Forest Floor',
                        'Upper, Middle, Lower, Ground',
                        'Trees, Plants, Grass, Soil',
                        'Sky, Trees, Plants, Soil'
                    ]
                },
                'correct_option': 0,
                'explanation': {
                    'en': 'The canopy, understory, and forest floor layers with emergent trees above',
                    'ms': 'Lapisan kanopi, lapisan bawah, dan lantai hutan dengan pokok muncul di atas',
                    'zh': '冠层、林下层和森林地面，上方有突出的树木'
                },
                'order': 1
            },
        ]
        
        for quiz_data_item in quiz_data:
            ARQuizQuestion.objects.create(**quiz_data_item)
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(quiz_data)} quiz questions'))
        
        # Create Badges
        badges_data = [
            {
                'badge_id': 'forest_explorer',
                'name': 'Forest Explorer',
                'description': {
                    'en': 'Visited all forest biodiversity hotspots',
                    'ms': 'Melawati semua titik panas biodiversiti hutan',
                    'zh': '访问了所有森林生物多样性热点'
                },
                'icon': 'leaf',
                'requirement': 'Visit 12 forest hotspots'
            },
            {
                'badge_id': 'quiz_master',
                'name': 'Quiz Master',
                'description': {
                    'en': 'Score 90% or above on 3 quizzes',
                    'ms': 'Skorkan 90% atau lebih tinggi pada 3 kuiz',
                    'zh': '在3个测验上得分90%或以上'
                },
                'icon': 'trophy',
                'requirement': 'Score 90%+ on 3 quizzes'
            },
            {
                'badge_id': 'safety_expert',
                'name': 'Wildlife Safety Expert',
                'description': {
                    'en': 'Complete wildlife safety training',
                    'ms': 'Selesaikan latihan keselamatan hidupan liar',
                    'zh': '完成野生动物安全培训'
                },
                'icon': 'shield-check',
                'requirement': 'Complete wildlife safety training'
            },
        ]
        
        for badge_data in badges_data:
            ARBadge.objects.create(**badge_data)
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(badges_data)} badges'))
        self.stdout.write(self.style.SUCCESS('\n✓ AR Training sample data created successfully!'))
