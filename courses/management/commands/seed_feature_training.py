from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models.signals import post_save

from ar_training.models import ARScenario
from ar_training.seed_data import TRAINING_IMAGE, ensure_seed_data
from courses.models import Chapter, Course, Lesson, PracticeExercise, Quiz
from user_progress.models import Badge
from user_progress.services import sync_all_badges_for_all_users
from user_progress.signals import sync_badges_when_badge_changes


IMAGE_LIBRARY = {
    'safety': 'https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=1200',
    'security': 'https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=1200',
    'offline': 'https://images.unsplash.com/photo-1452421822248-d4c2b47f0c81?w=1200',
    'first_aid': 'https://images.unsplash.com/photo-1581056771107-24ca5f033842?w=1200',
    'communication': 'https://images.unsplash.com/photo-1521737604893-d14cc237f11d?w=1200',
    'bako': 'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=1200',
    'coast': 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1200',
    'wildlife': TRAINING_IMAGE,
    'semenggoh': 'https://images.unsplash.com/photo-1540573133985-87b6da6d54a9?w=1200',
}


GENERAL_CATALOG = [
    {
        'code': 'general-guide-foundations-101',
        'tags': ['General', 'Orientation', 'Professional Skills'],
        'image': 'communication',
        'title': 'Professional Park Guide Foundations',
        'summary': 'Build the core mindset, ethics, visitor care, and daily workflow expected from a professional park guide.',
        'chapters': [
            ('Guide Role and Duty of Care', ['Professional responsibilities', 'Visitor expectations', 'Daily briefing workflow']),
            ('Visitor Experience Basics', ['Welcoming a group', 'Reading visitor needs', 'Closing a tour professionally']),
            ('Ethics and Conservation Conduct', ['Guide code of conduct', 'Respectful interpretation', 'Reporting concerns']),
        ],
    },
    {
        'code': 'general-safety-response-102',
        'tags': ['General', 'Safety', 'Emergency'],
        'image': 'first_aid',
        'title': 'Trail Safety and Emergency Response',
        'summary': 'Practise hazard scanning, first response decisions, communication trees, and incident documentation.',
        'chapters': [
            ('Hazard Awareness', ['Trail risk scanning', 'Weather and terrain decisions', 'Visitor health cues']),
            ('Emergency First Response', ['Stop and assess', 'Call for support', 'Evacuation handover']),
            ('Incident Reporting', ['What to record', 'Evidence and privacy', 'After-action review']),
        ],
    },
    {
        'code': 'general-visitor-communication-103',
        'tags': ['General', 'Communication', 'Interpretation'],
        'image': 'communication',
        'title': 'Visitor Communication and Interpretation',
        'summary': 'Turn facts into memorable explanations, manage group behaviour, and adapt language for different visitors.',
        'chapters': [
            ('Interpretation Design', ['Theme-based guiding', 'Story structure', 'Question prompts']),
            ('Group Management', ['Pacing and positioning', 'Managing interruptions', 'Inclusive communication']),
            ('Difficult Conversations', ['Correcting unsafe behaviour', 'De-escalation language', 'Cultural sensitivity']),
        ],
    },
    {
        'code': 'general-digital-security-104',
        'tags': ['General', 'Security', 'Account Safety'],
        'image': 'security',
        'title': 'Digital Safety and Secure App Use',
        'summary': 'Use passkeys, authenticator codes, secure files, and careful data handling while working in the field.',
        'chapters': [
            ('Secure Sign-in', ['Password hygiene', 'Passkeys and 2FA', 'Lost-device reporting']),
            ('Sensitive Data Handling', ['Visitor and staff privacy', 'Evidence handling', 'Safe sharing rules']),
            ('App Reliability', ['Session refresh behaviour', 'Network error handling', 'When to report app issues']),
        ],
    },
    {
        'code': 'general-offline-field-105',
        'tags': ['General', 'Offline', 'Field Readiness'],
        'image': 'offline',
        'title': 'Offline Field Readiness',
        'summary': 'Prepare maps, downloaded materials, emergency contacts, and backup workflows before entering low-signal areas.',
        'chapters': [
            ('Before Leaving Base', ['Download required materials', 'Verify maps and files', 'Battery and device checks']),
            ('Low-Signal Operations', ['Working from cached content', 'Recording notes offline', 'Syncing after coverage returns']),
            ('Contingency Planning', ['Backup meeting points', 'Radio and phone handover', 'Escalation without data']),
        ],
    },
    {
        'code': 'general-ar-field-simulations-106',
        'tags': ['General', 'AR', 'Immersive', 'Simulation'],
        'image': 'wildlife',
        'title': 'Immersive AR Park Guide Training',
        'summary': 'Practise biodiversity interpretation, eco-tourism control, wildlife safety, conservation, and professional guiding through integrated AR lessons.',
        'ar_code_map': {
            'Launch AR biodiversity briefing': 'vr-biodiversity-canopy-briefing',
            'Launch AR eco-tourism trail control': 'ar-ecotourism-low-impact-trail',
            'Launch AR wildlife encounter drill': 'vr-wildlife-encounter-response',
        },
        'chapters': [
            ('AR Field Simulation Briefing', ['How AR lessons work', '360 hotspot review workflow', 'Field decision scoring']),
            ('Core AR Scenarios', ['Launch AR biodiversity briefing', 'Launch AR eco-tourism trail control', 'Launch AR wildlife encounter drill']),
            ('Debrief and Transfer', ['Translating AR decisions to live tours', 'Recording scenario learning', 'Preparing for park-specific AR drills']),
        ],
    },
]


PARK_CATALOG = [
    {
        'park': 'Bako',
        'code': 'bako-orientation-201',
        'tags': ['Park Specific', 'Bako', 'Orientation'],
        'image': 'bako',
        'title': 'Bako National Park Orientation',
        'summary': 'Learn Bako trail zones, visitor flow, coastal risk, park rules, and field briefing standards.',
        'chapters': [
            ('Bako Site Familiarity', ['Park identity and visitor profile', 'Trail zones and common stops', 'Jetty and arrival flow']),
            ('Bako Safety Briefing', ['Coastal and tide awareness', 'Heat and hydration', 'Group boundaries']),
            ('Bako Visitor Management', ['Permit checks', 'Trail pacing', 'End-of-tour handover']),
        ],
    },
    {
        'park': 'Bako',
        'code': 'bako-biodiversity-ar-202',
        'tags': ['Park Specific', 'Bako', 'Biodiversity', 'AR'],
        'image': 'wildlife',
        'ar_code': 'vr-biodiversity-canopy-briefing',
        'title': 'Bako Rainforest Biodiversity with AR',
        'summary': 'Use AR to practise explaining forest layers, plant adaptation, regeneration, and low-impact observation.',
        'chapters': [
            ('Forest Layer Interpretation', ['Canopy and understory roles', 'Forest floor nutrient cycle', 'Low-impact observation']),
            ('AR Biodiversity Practice', ['Scenario briefing', 'Launch AR hotspot review', 'Decision debrief']),
            ('Visitor Questions', ['Answering ecology questions', 'Correcting misconceptions', 'Connecting species relationships']),
        ],
    },
    {
        'park': 'Bako',
        'code': 'bako-coastal-ecotourism-203',
        'tags': ['Park Specific', 'Bako', 'Eco-tourism'],
        'image': 'coast',
        'title': 'Bako Coastal Eco-tourism Control',
        'summary': 'Practise viewpoint control, photo boundaries, waste prevention, boardwalk etiquette, and leave-no-trace language.',
        'chapters': [
            ('Coastal Visitor Flow', ['Photo stop boundaries', 'Boardwalk congestion', 'Viewpoint timing']),
            ('Eco-tourism Practice', ['Scenario briefing', 'Trail control role-play', 'Decision debrief']),
            ('Leave No Trace Coaching', ['Waste messaging', 'Noise and wildlife impact', 'Positive visitor reminders']),
        ],
    },
    {
        'park': 'Bako',
        'code': 'bako-wildlife-response-204',
        'tags': ['Park Specific', 'Bako', 'Wildlife', 'Safety'],
        'image': 'wildlife',
        'title': 'Bako Wildlife Encounter Response',
        'summary': 'Rehearse macaque and trail wildlife response: safe distance, no feeding, calm crowd control, rerouting, and escalation.',
        'chapters': [
            ('Wildlife Risk Cues', ['Animal stress signals', 'Visitor food risk', 'Distance and noise']),
            ('Wildlife Response Drill', ['Scenario briefing', 'Encounter response role-play', 'Decision debrief']),
            ('After-Encounter Reporting', ['What to report', 'Visitor education follow-up', 'Route status updates']),
        ],
    },
    {
        'park': 'Semenggoh',
        'code': 'semenggoh-orientation-301',
        'tags': ['Park Specific', 'Semenggoh', 'Orientation'],
        'image': 'semenggoh',
        'title': 'Semenggoh Wildlife Centre Orientation',
        'summary': 'Learn centre purpose, visitor flow, feeding-area conduct, ranger boundaries, and conservation messaging.',
        'chapters': [
            ('Centre Role and Layout', ['Conservation purpose', 'Visitor zones', 'Ranger and guide roles']),
            ('Viewing Area Protocol', ['Quiet positioning', 'Barrier discipline', 'Photo and movement rules']),
            ('Daily Visitor Briefing', ['Opening safety message', 'Expectation setting', 'Exit and feedback flow']),
        ],
    },
    {
        'park': 'Semenggoh',
        'code': 'semenggoh-orangutan-behaviour-302',
        'tags': ['Park Specific', 'Semenggoh', 'Orangutan', 'Wildlife', 'AR'],
        'image': 'semenggoh',
        'ar_code': 'vr-wildlife-encounter-response',
        'title': 'Semenggoh Orangutan Behaviour and Safety with AR',
        'summary': 'Teach orangutan behaviour, viewing etiquette, safe distance, visitor silence, and no-feeding expectations.',
        'chapters': [
            ('Orangutan Behaviour Basics', ['Movement and feeding cues', 'Stress signs', 'Mother-infant sensitivity']),
            ('AR Wildlife Safety Practice', ['Scenario briefing', 'Launch AR response drill', 'Decision debrief']),
            ('Visitor Etiquette Coaching', ['Silence and stillness', 'Camera behaviour', 'Food and bag control']),
        ],
    },
    {
        'park': 'Semenggoh',
        'code': 'semenggoh-conservation-storytelling-303',
        'tags': ['Park Specific', 'Semenggoh', 'Conservation', 'Interpretation'],
        'image': 'semenggoh',
        'title': 'Semenggoh Conservation Storytelling',
        'summary': 'Build respectful, accurate conservation stories around rehabilitation, habitat protection, and visitor responsibility.',
        'chapters': [
            ('Conservation Narrative', ['Rehabilitation message', 'Habitat protection', 'Human-wildlife responsibility']),
            ('Sensitive Storytelling', ['Avoiding sensational claims', 'Respectful animal language', 'Answering hard questions']),
            ('Call-to-Action Design', ['Visitor pledges', 'Donation and support messaging', 'Post-visit behaviour']),
        ],
    },
    {
        'park': 'Semenggoh',
        'code': 'semenggoh-crowd-operations-304',
        'tags': ['Park Specific', 'Semenggoh', 'Crowd Control', 'Operations'],
        'image': 'semenggoh',
        'title': 'Semenggoh Crowd and Viewing Operations',
        'summary': 'Manage busy viewing periods, guide positioning, late arrivals, accessibility needs, and safe exits.',
        'chapters': [
            ('Crowd Flow Planning', ['Arrival grouping', 'Viewing rotation', 'Late visitor handling']),
            ('Accessible Guiding', ['Mobility-aware positioning', 'Clear audio delivery', 'Alternative viewing support']),
            ('Exit and Incident Control', ['Safe dispersal', 'Missing visitor checks', 'Incident notes']),
        ],
    },
]


TRANSLATIONS = {
    'Professional Park Guide Foundations': {
        'ms': 'Asas Profesional Panduan Taman',
        'zh': '专业公园导览基础',
    },
    'Build the core mindset, ethics, visitor care, and daily workflow expected from a professional park guide.': {
        'ms': 'Bina pemikiran asas, etika, penjagaan pelawat, dan aliran kerja harian yang diperlukan oleh panduan taman profesional.',
        'zh': '建立专业公园导览员所需的核心思维、伦理、访客照护和日常工作流程。',
    },
    'Trail Safety and Emergency Response': {
        'ms': 'Keselamatan Denai dan Tindak Balas Kecemasan',
        'zh': '步道安全与紧急应对',
    },
    'Practise hazard scanning, first response decisions, communication trees, and incident documentation.': {
        'ms': 'Latih pengesanan bahaya, keputusan tindak balas awal, aliran komunikasi, dan dokumentasi insiden.',
        'zh': '练习危险识别、初步应对决策、沟通流程和事故记录。',
    },
    'Visitor Communication and Interpretation': {
        'ms': 'Komunikasi Pelawat dan Interpretasi',
        'zh': '访客沟通与讲解',
    },
    'Turn facts into memorable explanations, manage group behaviour, and adapt language for different visitors.': {
        'ms': 'Tukar fakta kepada penerangan yang mudah diingati, urus tingkah laku kumpulan, dan sesuaikan bahasa untuk pelawat berbeza.',
        'zh': '把事实转化为易记的讲解，管理团队行为，并为不同访客调整表达方式。',
    },
    'Digital Safety and Secure App Use': {
        'ms': 'Keselamatan Digital dan Penggunaan Aplikasi Selamat',
        'zh': '数字安全与安全使用应用',
    },
    'Use passkeys, authenticator codes, secure files, and careful data handling while working in the field.': {
        'ms': 'Gunakan passkey, kod pengesah, fail selamat, dan pengendalian data yang teliti semasa bekerja di lapangan.',
        'zh': '在户外工作时使用通行密钥、验证器代码、安全文件，并谨慎处理数据。',
    },
    'Offline Field Readiness': {
        'ms': 'Persediaan Lapangan Luar Talian',
        'zh': '离线现场准备',
    },
    'Prepare maps, downloaded materials, emergency contacts, and backup workflows before entering low-signal areas.': {
        'ms': 'Sediakan peta, bahan dimuat turun, kenalan kecemasan, dan aliran kerja sandaran sebelum memasuki kawasan isyarat lemah.',
        'zh': '进入低信号区域前，准备地图、已下载资料、紧急联系人和备用流程。',
    },
    'Immersive AR Park Guide Training': {
        'ms': 'Latihan AR Imersif Pemandu Taman',
        'zh': '沉浸式 AR 公园导游培训',
    },
    'Practise biodiversity interpretation, eco-tourism control, wildlife safety, conservation, and professional guiding through integrated AR lessons.': {
        'ms': 'Latih interpretasi biodiversiti, kawalan eko-pelancongan, keselamatan hidupan liar, pemuliharaan, dan panduan profesional melalui pelajaran AR bersepadu.',
        'zh': '通过整合式 AR 课程练习生物多样性讲解、生态旅游管控、野生动物安全、保育和专业导览。',
    },
    'Bako National Park Orientation': {
        'ms': 'Orientasi Taman Negara Bako',
        'zh': '巴哥国家公园导览',
    },
    'Learn Bako trail zones, visitor flow, coastal risk, park rules, and field briefing standards.': {
        'ms': 'Pelajari zon denai Bako, aliran pelawat, risiko pesisir, peraturan taman, dan piawaian taklimat lapangan.',
        'zh': '学习巴哥步道分区、访客动线、海岸风险、公园规则和现场简报标准。',
    },
    'Bako Rainforest Biodiversity with AR': {
        'ms': 'Biodiversiti Hutan Hujan Bako dengan AR',
        'zh': '巴哥雨林生物多样性 AR 课程',
    },
    'Use AR to practise explaining forest layers, plant adaptation, regeneration, and low-impact observation.': {
        'ms': 'Gunakan AR untuk melatih penerangan lapisan hutan, adaptasi tumbuhan, regenerasi, dan pemerhatian berimpak rendah.',
        'zh': '使用 AR 练习讲解森林层次、植物适应、再生过程和低影响观察。',
    },
    'Bako Coastal Eco-tourism Control': {
        'ms': 'Kawalan Eko-pelancongan Pesisir Bako',
        'zh': '巴哥海岸生态旅游管控',
    },
    'Practise viewpoint control, photo boundaries, waste prevention, boardwalk etiquette, and leave-no-trace language.': {
        'ms': 'Latih kawalan tempat tinjauan, sempadan fotografi, pencegahan sisa, etika laluan papan, dan bahasa tanpa jejak.',
        'zh': '练习观景点管控、拍照边界、垃圾预防、栈道礼仪和无痕旅游表达。',
    },
    'Bako Wildlife Encounter Response': {
        'ms': 'Tindak Balas Pertemuan Hidupan Liar Bako',
        'zh': '巴哥野生动物相遇应对',
    },
    'Rehearse macaque and trail wildlife response: safe distance, no feeding, calm crowd control, rerouting, and escalation.': {
        'ms': 'Latih tindak balas terhadap kera dan hidupan liar denai: jarak selamat, larangan memberi makan, kawalan orang ramai, lencongan, dan eskalasi.',
        'zh': '演练猕猴和步道野生动物应对：安全距离、禁止喂食、冷静控场、改道和升级通报。',
    },
    'Semenggoh Wildlife Centre Orientation': {
        'ms': 'Orientasi Pusat Hidupan Liar Semenggoh',
        'zh': '实蒙谷野生动物中心导览',
    },
    'Learn centre purpose, visitor flow, feeding-area conduct, ranger boundaries, and conservation messaging.': {
        'ms': 'Pelajari tujuan pusat, aliran pelawat, tingkah laku di kawasan pemberian makan, sempadan renjer, dan mesej pemuliharaan.',
        'zh': '学习中心宗旨、访客动线、喂食区行为规范、护林员边界和保育讯息。',
    },
    'Semenggoh Orangutan Behaviour and Safety with AR': {
        'ms': 'Tingkah Laku dan Keselamatan Orang Utan Semenggoh dengan AR',
        'zh': '实蒙谷红毛猩猩行为与安全 AR 课程',
    },
    'Teach orangutan behaviour, viewing etiquette, safe distance, visitor silence, and no-feeding expectations.': {
        'ms': 'Ajarkan tingkah laku orang utan, etika pemerhatian, jarak selamat, kesenyapan pelawat, dan larangan memberi makan.',
        'zh': '讲解红毛猩猩行为、观赏礼仪、安全距离、保持安静和禁止喂食要求。',
    },
    'Semenggoh Conservation Storytelling': {
        'ms': 'Penceritaan Pemuliharaan Semenggoh',
        'zh': '实蒙谷保育故事讲解',
    },
    'Build respectful, accurate conservation stories around rehabilitation, habitat protection, and visitor responsibility.': {
        'ms': 'Bina cerita pemuliharaan yang hormat dan tepat tentang rehabilitasi, perlindungan habitat, dan tanggungjawab pelawat.',
        'zh': '围绕康复、栖息地保护和访客责任，建立尊重且准确的保育故事。',
    },
    'Semenggoh Crowd and Viewing Operations': {
        'ms': 'Operasi Orang Ramai dan Pemerhatian Semenggoh',
        'zh': '实蒙谷人流与观赏运营',
    },
    'Manage busy viewing periods, guide positioning, late arrivals, accessibility needs, and safe exits.': {
        'ms': 'Urus waktu pemerhatian sibuk, kedudukan panduan, pelawat lewat, keperluan aksesibiliti, dan keluar dengan selamat.',
        'zh': '管理繁忙观赏时段、导览站位、迟到访客、无障碍需求和安全离场。',
    },
}

PHRASE_TRANSLATIONS = {
    'Guide Role and Duty of Care': ('Peranan Panduan dan Tanggungjawab Penjagaan', '导览角色与照护责任'),
    'Visitor Experience Basics': ('Asas Pengalaman Pelawat', '访客体验基础'),
    'Ethics and Conservation Conduct': ('Etika dan Tingkah Laku Pemuliharaan', '伦理与保育行为'),
    'Hazard Awareness': ('Kesedaran Bahaya', '危险意识'),
    'Emergency First Response': ('Tindak Balas Awal Kecemasan', '紧急初步应对'),
    'Incident Reporting': ('Pelaporan Insiden', '事故报告'),
    'Interpretation Design': ('Reka Bentuk Interpretasi', '讲解设计'),
    'Group Management': ('Pengurusan Kumpulan', '团队管理'),
    'Difficult Conversations': ('Perbualan Sukar', '困难沟通'),
    'Secure Sign-in': ('Log Masuk Selamat', '安全登录'),
    'Sensitive Data Handling': ('Pengendalian Data Sensitif', '敏感数据处理'),
    'App Reliability': ('Kebolehpercayaan Aplikasi', '应用可靠性'),
    'Before Leaving Base': ('Sebelum Meninggalkan Pangkalan', '离开基地前'),
    'Low-Signal Operations': ('Operasi Isyarat Lemah', '低信号操作'),
    'Contingency Planning': ('Perancangan Kontingensi', '应急计划'),
    'AR Field Simulation Briefing': ('Taklimat Simulasi Lapangan AR', 'AR 实地模拟简报'),
    'Core AR Scenarios': ('Senario AR Teras', '核心 AR 场景'),
    'Debrief and Transfer': ('Rumusan dan Pemindahan Kemahiran', '复盘与迁移'),
    'Bako Site Familiarity': ('Kefahaman Tapak Bako', '熟悉巴哥场地'),
    'Bako Safety Briefing': ('Taklimat Keselamatan Bako', '巴哥安全简报'),
    'Bako Visitor Management': ('Pengurusan Pelawat Bako', '巴哥访客管理'),
    'Forest Layer Interpretation': ('Interpretasi Lapisan Hutan', '森林层次讲解'),
    'AR Biodiversity Practice': ('Latihan Biodiversiti AR', 'AR 生物多样性练习'),
    'Visitor Questions': ('Soalan Pelawat', '访客提问'),
    'Coastal Visitor Flow': ('Aliran Pelawat Pesisir', '海岸访客动线'),
    'Eco-tourism Practice': ('Latihan Eko-pelancongan', '生态旅游练习'),
    'Leave No Trace Coaching': ('Bimbingan Tanpa Jejak', '无痕旅游指导'),
    'Wildlife Risk Cues': ('Petunjuk Risiko Hidupan Liar', '野生动物风险线索'),
    'Wildlife Response Drill': ('Latihan Tindak Balas Hidupan Liar', '野生动物应对演练'),
    'After-Encounter Reporting': ('Pelaporan Selepas Pertemuan', '相遇后报告'),
    'Centre Role and Layout': ('Peranan dan Susun Atur Pusat', '中心角色与布局'),
    'Viewing Area Protocol': ('Protokol Kawasan Pemerhatian', '观赏区规程'),
    'Daily Visitor Briefing': ('Taklimat Harian Pelawat', '每日访客简报'),
    'Orangutan Behaviour Basics': ('Asas Tingkah Laku Orang Utan', '红毛猩猩行为基础'),
    'AR Wildlife Safety Practice': ('Latihan Keselamatan Hidupan Liar AR', 'AR 野生动物安全练习'),
    'Visitor Etiquette Coaching': ('Bimbingan Etika Pelawat', '访客礼仪指导'),
    'Conservation Narrative': ('Naratif Pemuliharaan', '保育叙事'),
    'Sensitive Storytelling': ('Penceritaan Sensitif', '敏感议题讲解'),
    'Call-to-Action Design': ('Reka Bentuk Seruan Bertindak', '行动号召设计'),
    'Crowd Flow Planning': ('Perancangan Aliran Orang Ramai', '人流规划'),
    'Accessible Guiding': ('Panduan Mesra Akses', '无障碍导览'),
    'Exit and Incident Control': ('Kawalan Keluar dan Insiden', '离场与事故控制'),
}

PHRASE_TRANSLATIONS.update({
    'Professional responsibilities': ('Tanggungjawab profesional', '专业职责'),
    'Visitor expectations': ('Jangkaan pelawat', '访客期望'),
    'Daily briefing workflow': ('Aliran kerja taklimat harian', '每日简报流程'),
    'Welcoming a group': ('Menyambut kumpulan', '迎接团队'),
    'Reading visitor needs': ('Mengenal pasti keperluan pelawat', '识别访客需求'),
    'Closing a tour professionally': ('Menamatkan lawatan secara profesional', '专业结束导览'),
    'Guide code of conduct': ('Kod tingkah laku panduan', '导览员行为准则'),
    'Respectful interpretation': ('Interpretasi yang hormat', '尊重式讲解'),
    'Reporting concerns': ('Melaporkan kebimbangan', '报告问题'),
    'Trail risk scanning': ('Imbasan risiko denai', '步道风险扫描'),
    'Weather and terrain decisions': ('Keputusan cuaca dan rupa bumi', '天气与地形决策'),
    'Visitor health cues': ('Petunjuk kesihatan pelawat', '访客健康信号'),
    'Stop and assess': ('Berhenti dan nilai', '停下并评估'),
    'Call for support': ('Memanggil bantuan', '请求支援'),
    'Evacuation handover': ('Serahan pemindahan', '撤离交接'),
    'What to record': ('Perkara yang perlu direkod', '需要记录的事项'),
    'Evidence and privacy': ('Bukti dan privasi', '证据与隐私'),
    'After-action review': ('Semakan selepas tindakan', '行动后复盘'),
    'Theme-based guiding': ('Panduan berasaskan tema', '主题式导览'),
    'Story structure': ('Struktur cerita', '故事结构'),
    'Question prompts': ('Dorongan soalan', '提问提示'),
    'Pacing and positioning': ('Rentak dan kedudukan', '节奏与站位'),
    'Managing interruptions': ('Mengurus gangguan', '处理中断'),
    'Inclusive communication': ('Komunikasi inklusif', '包容性沟通'),
    'Correcting unsafe behaviour': ('Membetulkan tingkah laku tidak selamat', '纠正不安全行为'),
    'De-escalation language': ('Bahasa meredakan keadaan', '降温沟通语言'),
    'Cultural sensitivity': ('Kepekaan budaya', '文化敏感度'),
    'Password hygiene': ('Amalan kata laluan selamat', '密码安全习惯'),
    'Passkeys and 2FA': ('Passkey dan 2FA', '通行密钥与双重验证'),
    'Lost-device reporting': ('Pelaporan peranti hilang', '遗失设备报告'),
    'Visitor and staff privacy': ('Privasi pelawat dan staf', '访客与员工隐私'),
    'Evidence handling': ('Pengendalian bukti', '证据处理'),
    'Safe sharing rules': ('Peraturan perkongsian selamat', '安全分享规则'),
    'Session refresh behaviour': ('Tingkah laku penyegaran sesi', '会话刷新行为'),
    'Network error handling': ('Pengendalian ralat rangkaian', '网络错误处理'),
    'When to report app issues': ('Bila melaporkan isu aplikasi', '何时报告应用问题'),
    'Download required materials': ('Muat turun bahan diperlukan', '下载所需资料'),
    'Verify maps and files': ('Sahkan peta dan fail', '核对地图和文件'),
    'Battery and device checks': ('Semakan bateri dan peranti', '电量与设备检查'),
    'Working from cached content': ('Bekerja dengan kandungan cache', '使用缓存内容工作'),
    'Recording notes offline': ('Merekod nota luar talian', '离线记录笔记'),
    'Syncing after coverage returns': ('Menyegerak selepas isyarat kembali', '信号恢复后同步'),
    'Backup meeting points': ('Titik pertemuan sandaran', '备用集合点'),
    'Radio and phone handover': ('Serahan radio dan telefon', '无线电与电话交接'),
    'Escalation without data': ('Eskalasi tanpa data', '无数据时升级通报'),
    'How AR lessons work': ('Cara pelajaran AR berfungsi', 'AR 课程如何运作'),
    '360 hotspot review workflow': ('Aliran semakan hotspot 360', '360 热点复习流程'),
    'Field decision scoring': ('Pemarkahan keputusan lapangan', '现场决策评分'),
    'Launch AR biodiversity briefing': ('Lancarkan taklimat biodiversiti AR', '启动 AR 生物多样性简报'),
    'Launch AR eco-tourism trail control': ('Lancarkan kawalan denai eko-pelancongan AR', '启动 AR 生态旅游步道管控'),
    'Launch AR wildlife encounter drill': ('Lancarkan latihan pertemuan hidupan liar AR', '启动 AR 野生动物相遇演练'),
    'Translating AR decisions to live tours': ('Menterjemah keputusan AR kepada lawatan sebenar', '把 AR 决策迁移到真实导览'),
    'Recording scenario learning': ('Merekod pembelajaran senario', '记录场景学习成果'),
    'Preparing for park-specific AR drills': ('Bersedia untuk latihan AR khusus taman', '准备公园专项 AR 演练'),
    'Park identity and visitor profile': ('Identiti taman dan profil pelawat', '公园定位与访客画像'),
    'Trail zones and common stops': ('Zon denai dan hentian biasa', '步道分区与常见停靠点'),
    'Jetty and arrival flow': ('Jeti dan aliran ketibaan', '码头与抵达动线'),
    'Coastal and tide awareness': ('Kesedaran pesisir dan pasang surut', '海岸与潮汐意识'),
    'Heat and hydration': ('Haba dan hidrasi', '高温与补水'),
    'Group boundaries': ('Sempadan kumpulan', '团队边界'),
    'Permit checks': ('Semakan permit', '许可证检查'),
    'Trail pacing': ('Rentak denai', '步道节奏'),
    'End-of-tour handover': ('Serahan akhir lawatan', '导览结束交接'),
    'Canopy and understory roles': ('Peranan kanopi dan bawah kanopi', '树冠层与林下层作用'),
    'Forest floor nutrient cycle': ('Kitaran nutrien lantai hutan', '森林地表养分循环'),
    'Low-impact observation': ('Pemerhatian berimpak rendah', '低影响观察'),
    'Scenario briefing': ('Taklimat senario', '情境简报'),
    'Launch AR hotspot review': ('Mulakan semakan hotspot AR', '启动 AR 热点复习'),
    'Decision debrief': ('Rumusan keputusan', '决策复盘'),
    'Answering ecology questions': ('Menjawab soalan ekologi', '回答生态问题'),
    'Correcting misconceptions': ('Membetulkan salah faham', '纠正误解'),
    'Connecting species relationships': ('Menghubungkan hubungan spesies', '连接物种关系'),
    'Photo stop boundaries': ('Sempadan hentian foto', '拍照点边界'),
    'Boardwalk congestion': ('Kesesakan laluan papan', '栈道拥堵'),
    'Viewpoint timing': ('Masa di tempat tinjauan', '观景点时间控制'),
    'Trail control role-play': ('Lakon peranan kawalan denai', '步道管控角色演练'),
    'Waste messaging': ('Mesej pencegahan sisa', '垃圾预防讯息'),
    'Noise and wildlife impact': ('Bunyi dan kesan terhadap hidupan liar', '噪音与野生动物影响'),
    'Positive visitor reminders': ('Peringatan positif kepada pelawat', '正向访客提醒'),
    'Animal stress signals': ('Isyarat tekanan haiwan', '动物压力信号'),
    'Visitor food risk': ('Risiko makanan pelawat', '访客食物风险'),
    'Distance and noise': ('Jarak dan bunyi', '距离与噪音'),
    'Encounter response role-play': ('Lakon peranan tindak balas pertemuan', '相遇应对角色演练'),
    'Visitor education follow-up': ('Susulan pendidikan pelawat', '访客教育跟进'),
    'Route status updates': ('Kemas kini status laluan', '路线状态更新'),
    'Conservation purpose': ('Tujuan pemuliharaan', '保育目的'),
    'Visitor zones': ('Zon pelawat', '访客区域'),
    'Ranger and guide roles': ('Peranan renjer dan panduan', '护林员与导览角色'),
    'Quiet positioning': ('Kedudukan senyap', '安静站位'),
    'Barrier discipline': ('Disiplin penghadang', '栏杆边界纪律'),
    'Photo and movement rules': ('Peraturan foto dan pergerakan', '拍照与移动规则'),
    'Opening safety message': ('Mesej keselamatan pembukaan', '开场安全讯息'),
    'Expectation setting': ('Penetapan jangkaan', '设定期望'),
    'Exit and feedback flow': ('Aliran keluar dan maklum balas', '离场与反馈流程'),
    'Movement and feeding cues': ('Petunjuk pergerakan dan makan', '移动与进食线索'),
    'Stress signs': ('Tanda tekanan', '压力迹象'),
    'Mother-infant sensitivity': ('Kepekaan ibu dan anak', '母婴敏感性'),
    'Launch AR response drill': ('Mulakan latihan tindak balas AR', '启动 AR 应对演练'),
    'Silence and stillness': ('Senyap dan tenang', '安静与静止'),
    'Camera behaviour': ('Tingkah laku kamera', '相机使用行为'),
    'Food and bag control': ('Kawalan makanan dan beg', '食物与包袋管控'),
    'Rehabilitation message': ('Mesej rehabilitasi', '康复讯息'),
    'Habitat protection': ('Perlindungan habitat', '栖息地保护'),
    'Human-wildlife responsibility': ('Tanggungjawab manusia dan hidupan liar', '人与野生动物责任'),
    'Avoiding sensational claims': ('Mengelakkan dakwaan sensasi', '避免夸张说法'),
    'Respectful animal language': ('Bahasa haiwan yang hormat', '尊重动物的表达'),
    'Answering hard questions': ('Menjawab soalan sukar', '回答困难问题'),
    'Visitor pledges': ('Ikrar pelawat', '访客承诺'),
    'Donation and support messaging': ('Mesej derma dan sokongan', '捐助与支持讯息'),
    'Post-visit behaviour': ('Tingkah laku selepas lawatan', '参观后行为'),
    'Arrival grouping': ('Pengumpulan ketibaan', '抵达分组'),
    'Viewing rotation': ('Giliran pemerhatian', '观赏轮换'),
    'Late visitor handling': ('Pengendalian pelawat lewat', '迟到访客处理'),
    'Mobility-aware positioning': ('Kedudukan mesra mobiliti', '考虑行动能力的站位'),
    'Clear audio delivery': ('Penyampaian audio jelas', '清晰声音传达'),
    'Alternative viewing support': ('Sokongan pemerhatian alternatif', '替代观赏支持'),
    'Safe dispersal': ('Penyuraian selamat', '安全疏散'),
    'Missing visitor checks': ('Semakan pelawat hilang', '失踪访客检查'),
    'Incident notes': ('Nota insiden', '事故记录'),
})


AUTO_TRANSLATIONS = {
    'Short supporting briefing video for class demonstration.': {
        'ms': 'Video taklimat sokongan ringkas untuk demonstrasi kelas.',
        'zh': '用于课堂演示的简短辅助简报视频。',
    },
    'Apply the lesson to realistic guide decisions.': {
        'ms': 'Aplikasikan pelajaran kepada keputusan panduan yang realistik.',
        'zh': '把课程内容应用到真实的导览决策中。',
    },
    'Check readiness before moving to the next chapter.': {
        'ms': 'Semak kesediaan sebelum beralih ke bab seterusnya.',
        'zh': '进入下一章前检查准备程度。',
    },
    'Give a short, practical explanation connected to visitor safety and conservation.': {
        'ms': 'Berikan penerangan ringkas dan praktikal yang dikaitkan dengan keselamatan pelawat dan pemuliharaan.',
        'zh': '给出简短实用的解释，并联系访客安全和保育。',
    },
    'Tell the visitor to read the sign later.': {
        'ms': 'Suruh pelawat membaca papan tanda kemudian.',
        'zh': '叫访客之后自己看告示牌。',
    },
    'Ignore the question to keep the group moving.': {
        'ms': 'Abaikan soalan untuk memastikan kumpulan terus bergerak.',
        'zh': '为了让团队继续前进而忽略问题。',
    },
    'Give a long technical lecture before checking the group.': {
        'ms': 'Berikan kuliah teknikal yang panjang sebelum memeriksa keadaan kumpulan.',
        'zh': '在确认团队状况前先进行冗长的技术讲解。',
    },
    'Set clear expectations, monitor the group, and adjust calmly.': {
        'ms': 'Tetapkan jangkaan yang jelas, pantau kumpulan, dan sesuaikan tindakan dengan tenang.',
        'zh': '设定清楚的期望，观察团队状况，并冷静调整。',
    },
    'Wait until a problem becomes serious.': {
        'ms': 'Tunggu sehingga masalah menjadi serius.',
        'zh': '等到问题变严重才处理。',
    },
    'Let visitors decide all boundaries themselves.': {
        'ms': 'Biarkan pelawat menentukan semua batasan sendiri.',
        'zh': '让访客自己决定所有边界。',
    },
    'Focus only on finishing quickly.': {
        'ms': 'Fokus hanya untuk menamatkan lawatan dengan cepat.',
        'zh': '只专注于尽快结束导览。',
    },
    'Time, location, people involved, action taken, and follow-up needed.': {
        'ms': 'Masa, lokasi, individu terlibat, tindakan yang diambil, dan susulan yang diperlukan.',
        'zh': '时间、地点、涉及人员、已采取的行动，以及需要跟进的事项。',
    },
    'Only the guide name.': {
        'ms': 'Hanya nama panduan.',
        'zh': '只记录导览员姓名。',
    },
    'Only photos, with no explanation.': {
        'ms': 'Hanya gambar tanpa sebarang penerangan.',
        'zh': '只记录照片，不附说明。',
    },
    'Nothing unless a visitor complains.': {
        'ms': 'Tidak perlu merekod apa-apa kecuali pelawat membuat aduan.',
        'zh': '除非访客投诉，否则什么都不用记录。',
    },
    'To help guides make safe, clear, visitor-ready decisions.': {
        'ms': 'Untuk membantu panduan membuat keputusan yang selamat, jelas, dan sesuai untuk pelawat.',
        'zh': '帮助导览员做出安全、清楚、适合访客的决策。',
    },
    'To memorise facts without field application.': {
        'ms': 'Untuk menghafal fakta tanpa aplikasi lapangan.',
        'zh': '只记忆事实而不应用到现场。',
    },
    'To replace ranger instructions.': {
        'ms': 'Untuk menggantikan arahan renjer.',
        'zh': '取代护林员的指示。',
    },
    'To make tours shorter at all costs.': {
        'ms': 'Untuk memendekkan lawatan walau apa pun keadaan.',
        'zh': '不惜一切让导览变短。',
    },
    'Pause, gather the group, restate the boundary, and explain the reason.': {
        'ms': 'Berhenti seketika, kumpulkan kumpulan, nyatakan semula batasan, dan jelaskan sebabnya.',
        'zh': '暂停，集合团队，重申边界，并解释原因。',
    },
    'Shout from far away.': {
        'ms': 'Menjerit dari jauh.',
        'zh': '从远处大喊。',
    },
    'Leave them and continue with the rest.': {
        'ms': 'Tinggalkan mereka dan teruskan dengan pelawat lain.',
        'zh': '留下他们，继续带其他人前进。',
    },
    'Cancel the entire tour immediately.': {
        'ms': 'Batalkan keseluruhan lawatan serta-merta.',
        'zh': '立刻取消整个导览。',
    },
    'Short, accurate, observable, and connected to what visitors can see.': {
        'ms': 'Ringkas, tepat, boleh diperhatikan, dan berkaitan dengan perkara yang dapat dilihat oleh pelawat.',
        'zh': '简短、准确、可观察，并与访客眼前看到的内容相关。',
    },
    'Highly technical with no examples.': {
        'ms': 'Terlalu teknikal tanpa contoh.',
        'zh': '非常技术化，而且没有例子。',
    },
    'Only jokes and entertainment.': {
        'ms': 'Hanya jenaka dan hiburan.',
        'zh': '只有玩笑和娱乐。',
    },
    'No explanation unless asked twice.': {
        'ms': 'Tidak memberi penerangan kecuali ditanya dua kali.',
        'zh': '除非被问两次，否则不解释。',
    },
    'Use downloaded/offline notes and report the sync issue after coverage returns.': {
        'ms': 'Gunakan nota yang telah dimuat turun/luar talian dan laporkan isu penyegerakan selepas liputan kembali.',
        'zh': '使用已下载/离线笔记，并在信号恢复后报告同步问题。',
    },
    'Invent missing procedures.': {
        'ms': 'Mereka prosedur yang tiada.',
        'zh': '自行编造缺失的流程。',
    },
    'Ignore the planned briefing.': {
        'ms': 'Abaikan taklimat yang dirancang.',
        'zh': '忽略原本计划的简报。',
    },
    'Ask visitors to search online.': {
        'ms': 'Minta pelawat mencari sendiri dalam talian.',
        'zh': '要求访客自己上网搜索。',
    },
    'Required lessons and assessments are completed to the passing standard.': {
        'ms': 'Pelajaran dan penilaian wajib diselesaikan mengikut standard lulus.',
        'zh': '完成必要课程和评估，并达到通过标准。',
    },
    'Opening the course once.': {
        'ms': 'Membuka kursus sekali sahaja.',
        'zh': '只打开课程一次。',
    },
    'Only viewing the thumbnail.': {
        'ms': 'Hanya melihat gambar kecil.',
        'zh': '只查看缩略图。',
    },
    'Skipping to the final badge screen.': {
        'ms': 'Melangkau terus ke skrin lencana akhir.',
        'zh': '直接跳到最终徽章页面。',
    },
}


def i18n(en, ms=None, zh=None):
    if isinstance(en, dict):
        return {
            'en': en.get('en') or '',
            'ms': ms or en.get('ms') or en.get('en') or '',
            'zh': zh or en.get('zh') or en.get('en') or '',
        }

    translated = TRANSLATIONS.get(en)
    if translated:
        return {'en': en, 'ms': ms or translated['ms'], 'zh': zh or translated['zh']}

    phrase = PHRASE_TRANSLATIONS.get(en)
    if phrase:
        return {'en': en, 'ms': ms or phrase[0], 'zh': zh or phrase[1]}

    auto = AUTO_TRANSLATIONS.get(en)
    if auto:
        return {'en': en, 'ms': ms or auto['ms'], 'zh': zh or auto['zh']}

    return {'en': en, 'ms': ms or en, 'zh': zh or en}


def localized(value, language='en', fallback=''):
    if isinstance(value, dict):
        return value.get(language) or value.get('en') or fallback
    return value or fallback


def phrase(en, language='en'):
    return localized(i18n(en), language)


def lesson_content_i18n(course_title, chapter_title, lesson_title, course_summary, is_ar=False):
    values = {}
    for lang in ('en', 'ms', 'zh'):
        lesson = phrase(lesson_title, lang)
        course = phrase(course_title, lang)
        chapter = phrase(chapter_title, lang)
        summary = phrase(course_summary, lang)

        if lang == 'ms':
            text = (
                f'{lesson} ialah sebahagian daripada {course}. '
                f'{summary} Dalam pelajaran ini, panduan melatih bahasa lapangan, titik keputusan, '
                f'dan tindakan berhadapan pelawat untuk {chapter.lower()}.'
            )
            if is_ar:
                text += ' Lancarkan aktiviti AR bersepadu, semak setiap hotspot, dan kaitkan setiap keputusan dengan pengurusan pelawat sebenar.'
        elif lang == 'zh':
            text = (
                f'{lesson} 是 {course} 的一部分。'
                f'{summary} 在本课中，导览员将练习现场表达、决策点，以及针对“{chapter}”的访客应对行动。'
            )
            if is_ar:
                text += ' 启动整合式 AR 活动，检查每个热点，并把每项决策连接回真实的访客管理情境。'
        else:
            text = (
                f'{lesson} is part of {course}. '
                f'{summary} In this lesson, guides practise field language, decision points, and visitor-facing actions for {chapter.lower()}.'
            )
            if is_ar:
                text += ' Launch the integrated AR activity, review every hotspot, and connect each decision back to real visitor management.'
        values[lang] = text
    return values


def chapter_description_i18n(chapter_title, course_title):
    return {
        'en': f'{phrase(chapter_title, "en")} for {phrase(course_title, "en")}.',
        'ms': f'{phrase(chapter_title, "ms")} untuk {phrase(course_title, "ms")}.',
        'zh': f'{phrase(chapter_title, "zh")}：{phrase(course_title, "zh")}。',
    }


def practice_title_i18n(chapter_title):
    return {
        'en': f'{phrase(chapter_title, "en")} Practice Scenarios',
        'ms': f'Senario Latihan {phrase(chapter_title, "ms")}',
        'zh': f'{phrase(chapter_title, "zh")}练习情境',
    }


def assessment_title_i18n(chapter_title):
    return {
        'en': f'{phrase(chapter_title, "en")} Assessment',
        'ms': f'Penilaian {phrase(chapter_title, "ms")}',
        'zh': f'{phrase(chapter_title, "zh")}评估',
    }


def field_briefing_title_i18n(lesson_title):
    return {
        'en': f'{phrase(lesson_title, "en")} field briefing',
        'ms': f'Taklimat lapangan {phrase(lesson_title, "ms")}',
        'zh': f'{phrase(lesson_title, "zh")}现场简报',
    }


def visitor_unsure_question_i18n(chapter_title):
    return {
        'en': f'A visitor is unsure why {phrase(chapter_title, "en").lower()} matters. What should the guide do?',
        'ms': f'Seorang pelawat tidak pasti mengapa {phrase(chapter_title, "ms").lower()} penting. Apakah yang patut dilakukan oleh panduan?',
        'zh': f'一名访客不明白为什么“{phrase(chapter_title, "zh")}”很重要。导览员应该怎么做？',
    }


def strongest_behaviour_question_i18n(course_title):
    return {
        'en': f'During {phrase(course_title, "en")}, which guide behaviour is strongest?',
        'ms': f'Semasa {phrase(course_title, "ms")}, tingkah laku panduan manakah yang paling baik?',
        'zh': f'在“{phrase(course_title, "zh")}”中，哪一种导览行为最合适？',
    }


def main_purpose_question_i18n(chapter_title):
    return {
        'en': f'What is the main purpose of {phrase(chapter_title, "en").lower()}?',
        'ms': f'Apakah tujuan utama {phrase(chapter_title, "ms").lower()}?',
        'zh': f'“{phrase(chapter_title, "zh")}”的主要目的是什么？',
    }


def answer_explanation_i18n(correct):
    correct_i18n = i18n(correct)
    return {
        'en': f'The best answer is: {correct_i18n["en"]}',
        'ms': f'Jawapan terbaik ialah: {correct_i18n["ms"]}',
        'zh': f'最佳答案是：{correct_i18n["zh"]}',
    }


def option_i18n(value, is_correct=False):
    text = i18n(value)
    return {
        'text': text,
        'label': text,
        'is_correct': is_correct,
    }


def question(prompt, correct, wrong_1, wrong_2, wrong_3=None):
    # Store repeated multilingual keys for compatibility with different frontend/API shapes.
    # Some screens read question_text, while older code may read question/text/prompt.
    prompt_i18n = i18n(prompt)
    options = [
        option_i18n(correct, True),
        option_i18n(wrong_1, False),
        option_i18n(wrong_2, False),
    ]
    if wrong_3:
        options.append(option_i18n(wrong_3, False))

    return {
        'question_text': prompt_i18n,
        'question': prompt_i18n,
        'text': prompt_i18n,
        'prompt': prompt_i18n,
        'question_type': 'multiple_choice',
        'options': options,
        'correctIndex': 0,
        'correct_index': 0,
        'explanation': answer_explanation_i18n(correct),
    }


def build_lesson(course_title, chapter_title, lesson_title, course_summary, image_key, ar_scenario=None, index=1):
    is_ar = ar_scenario is not None

    return {
        'title': i18n(lesson_title),
        'content_text': lesson_content_i18n(course_title, chapter_title, lesson_title, course_summary, is_ar=is_ar),
        'content_images': [ar_scenario.initial_panorama_url or TRAINING_IMAGE] if is_ar else [IMAGE_LIBRARY.get(image_key, IMAGE_LIBRARY['bako'])],
        'content_videos': [
            {
                'title': field_briefing_title_i18n(lesson_title),
                'url': 'https://www.youtube.com/watch?v=ysz5S6PUM-U',
                'description': i18n('Short supporting briefing video for class demonstration.'),
            }
        ] if index == 1 and not is_ar else [],
        'ar_scenario': ar_scenario,
        'estimated_time': 16 if is_ar else 12 + index,
    }


def get_lesson_ar_scenario(course_data, lesson_title):
    ar_code_map = course_data.get('ar_code_map') or {}
    scenario_code = ar_code_map.get(lesson_title)

    if not scenario_code and course_data.get('ar_code') and ('Launch AR' in lesson_title or 'AR ' in lesson_title):
        scenario_code = course_data.get('ar_code')

    if not scenario_code:
        return None

    return ARScenario.objects.filter(code=scenario_code).first()


def build_course_chapters(course_data):
    chapters = []

    for chapter_index, (chapter_title, lesson_titles) in enumerate(course_data['chapters'], start=1):
        lessons = []
        for lesson_index, lesson_title in enumerate(lesson_titles, start=1):
            lesson_scenario = get_lesson_ar_scenario(course_data, lesson_title)
            lessons.append(
                build_lesson(
                    course_data['title'],
                    chapter_title,
                    lesson_title,
                    course_data['summary'],
                    course_data['image'],
                    ar_scenario=lesson_scenario,
                    index=lesson_index,
                )
            )

        chapters.append({
            'title': i18n(chapter_title),
            'description': chapter_description_i18n(chapter_title, course_data['title']),
            'lessons': lessons,
            'exercises': [
                {
                    'title': practice_title_i18n(chapter_title),
                    'description': i18n('Apply the lesson to realistic guide decisions.'),
                    'exercise_type': 'mixed',
                    'passing_score': 70,
                    'questions': [
                        question(
                            visitor_unsure_question_i18n(chapter_title),
                            'Give a short, practical explanation connected to visitor safety and conservation.',
                            'Tell the visitor to read the sign later.',
                            'Ignore the question to keep the group moving.',
                            'Give a long technical lecture before checking the group.',
                        ),
                        question(
                            strongest_behaviour_question_i18n(course_data['title']),
                            'Set clear expectations, monitor the group, and adjust calmly.',
                            'Wait until a problem becomes serious.',
                            'Let visitors decide all boundaries themselves.',
                            'Focus only on finishing quickly.',
                        ),
                        question(
                            {
                                'en': 'What should be recorded after an unusual field situation?',
                                'ms': 'Apakah yang perlu direkod selepas situasi lapangan yang luar biasa?',
                                'zh': '现场发生异常情况后，应记录什么？',
                            },
                            'Time, location, people involved, action taken, and follow-up needed.',
                            'Only the guide name.',
                            'Only photos, with no explanation.',
                            'Nothing unless a visitor complains.',
                        ),
                    ],
                }
            ],
            'quizzes': [
                {
                    'title': assessment_title_i18n(chapter_title),
                    'description': i18n('Check readiness before moving to the next chapter.'),
                    'time_limit': 18,
                    'passing_score': 70,
                    'show_answers': True,
                    'questions': [
                        question(
                            main_purpose_question_i18n(chapter_title),
                            'To help guides make safe, clear, visitor-ready decisions.',
                            'To memorise facts without field application.',
                            'To replace ranger instructions.',
                            'To make tours shorter at all costs.',
                        ),
                        question(
                            {
                                'en': 'A group starts drifting outside the expected area. What is the best first response?',
                                'ms': 'Sebuah kumpulan mula bergerak keluar dari kawasan yang ditetapkan. Apakah tindak balas awal yang terbaik?',
                                'zh': '团队开始偏离指定区域。最好的第一反应是什么？',
                            },
                            'Pause, gather the group, restate the boundary, and explain the reason.',
                            'Shout from far away.',
                            'Leave them and continue with the rest.',
                            'Cancel the entire tour immediately.',
                        ),
                        question(
                            {
                                'en': 'Which explanation style is best for mixed visitor groups?',
                                'ms': 'Gaya penerangan manakah yang terbaik untuk kumpulan pelawat bercampur?',
                                'zh': '面对不同背景的访客群体，哪种讲解方式最好？',
                            },
                            'Short, accurate, observable, and connected to what visitors can see.',
                            'Highly technical with no examples.',
                            'Only jokes and entertainment.',
                            'No explanation unless asked twice.',
                        ),
                        question(
                            {
                                'en': 'If app materials are unavailable in the field, what should the guide do?',
                                'ms': 'Jika bahan aplikasi tidak tersedia di lapangan, apakah yang patut dilakukan oleh panduan?',
                                'zh': '如果在现场无法使用应用资料，导览员应该怎么做？',
                            },
                            'Use downloaded/offline notes and report the sync issue after coverage returns.',
                            'Invent missing procedures.',
                            'Ignore the planned briefing.',
                            'Ask visitors to search online.',
                        ),
                        question(
                            {
                                'en': 'What makes a course complete?',
                                'ms': 'Apakah yang menjadikan kursus lengkap?',
                                'zh': '怎样才算完成一门课程？',
                            },
                            'Required lessons and assessments are completed to the passing standard.',
                            'Opening the course once.',
                            'Only viewing the thumbnail.',
                            'Skipping to the final badge screen.',
                        ),
                    ],
                }
            ],
        })

    return chapters

def build_catalog():
    courses = []
    for item in GENERAL_CATALOG:
        courses.append({
            **item,
            'course_type': Course.COURSE_TYPE_GENERAL,
            'title_i18n': i18n(item['title']),
            'description_i18n': i18n(item['summary']),
        })

    for item in PARK_CATALOG:
        courses.append({
            **item,
            'course_type': Course.COURSE_TYPE_PARK_SPECIFIC,
            'title_i18n': i18n(item['title']),
            'description_i18n': i18n(item['summary']),
        })
    return courses


def feature_codes():
    return [item['code'] for item in build_catalog()]


def general_codes():
    return [item['code'] for item in GENERAL_CATALOG]


def archive_old_catalog(keep_codes):
    Course.objects.exclude(code__in=keep_codes).update(is_published=False)
    Badge.objects.filter(course__isnull=False).exclude(course__code__in=keep_codes).update(is_active=False)
    Badge.objects.filter(is_major_badge=True).exclude(name='Certified Bako and Semenggoh Guide Badge').update(is_active=False)


def delete_old_catalog(keep_codes):
    old_badges = Badge.objects.filter(course__isnull=False).exclude(course__code__in=keep_codes)
    old_badge_count = old_badges.count()
    old_badges.delete()
    old_courses = Course.objects.exclude(code__in=keep_codes)
    old_course_count = old_courses.count()
    old_courses.delete()
    Badge.objects.filter(is_major_badge=True).exclude(name='Certified Bako and Semenggoh Guide Badge').delete()
    return old_course_count, old_badge_count


def upsert_course(course_data):
    course = Course.objects.create(
        code=course_data['code'],
        title=course_data['title_i18n'],
        description=course_data['description_i18n'],
        thumbnail=IMAGE_LIBRARY.get(course_data['image'], TRAINING_IMAGE),
        course_type=course_data['course_type'],
        tags=course_data.get('tags', []),
        is_published=True,
    )

    if course.course_type == Course.COURSE_TYPE_PARK_SPECIFIC:
        course.prerequisites.set(Course.objects.filter(code__in=general_codes()))

    chapter_data = build_course_chapters(course_data)

    for chapter_index, raw_chapter in enumerate(chapter_data, start=1):
        chapter = Chapter.objects.create(
            course=course,
            order=chapter_index,
            title=raw_chapter['title'],
            description=raw_chapter['description'],
        )

        for lesson_index, raw_lesson in enumerate(raw_chapter['lessons'], start=1):
            Lesson.objects.create(
                chapter=chapter,
                order=lesson_index,
                title=raw_lesson['title'],
                content_text=raw_lesson['content_text'],
                content_images=raw_lesson['content_images'],
                content_videos=raw_lesson['content_videos'],
                ar_scenario=raw_lesson.get('ar_scenario'),
                estimated_time=raw_lesson['estimated_time'],
            )

        for exercise_index, raw_exercise in enumerate(raw_chapter['exercises'], start=1):
            PracticeExercise.objects.create(
                chapter=chapter,
                order=exercise_index,
                title=raw_exercise['title'],
                description=raw_exercise['description'],
                exercise_type=raw_exercise['exercise_type'],
                questions=raw_exercise['questions'],
                passing_score=raw_exercise['passing_score'],
            )

        for quiz_index, raw_quiz in enumerate(raw_chapter['quizzes'], start=1):
            Quiz.objects.create(
                chapter=chapter,
                order=quiz_index,
                title=raw_quiz['title'],
                description=raw_quiz['description'],
                questions=raw_quiz['questions'],
                passing_score=raw_quiz['passing_score'],
                time_limit=raw_quiz['time_limit'],
                show_answers=raw_quiz['show_answers'],
            )

    return course


def upsert_badge(course):
    name_translations = {
        'en': f'{localized(course.title)} Badge',
        'ms': f'Lencana {localized(course.title, "ms")}',
        'zh': f'{localized(course.title, "zh")}徽章',
    }
    description_translations = {
        'en': f'Awarded for completing the full {localized(course.title)} class.',
        'ms': f'Dianugerahkan selepas melengkapkan kelas penuh {localized(course.title, "ms")}.',
        'zh': f'完成“{localized(course.title, "zh")}”完整课程后获得。',
    }
    lesson_titles = list(
        Lesson.objects.filter(chapter__course=course)
        .order_by('chapter__order', 'order')
        .values_list('title__en', flat=True)
    )
    skill_titles = list(course.chapters.order_by('order').values_list('title__en', flat=True))

    defaults = {
        'name': name_translations['en'],
        'description': description_translations['en'],
        'name_translations': name_translations,
        'description_translations': description_translations,
        'badge_image_url': course.thumbnail or '',
        'badge_image_source': course.thumbnail or '',
        'skills_awarded': skill_titles,
        'lesson_highlights': lesson_titles[:8],
        'required_completed_modules': max(course.chapters.count(), 1),
        'required_badges_count': 0,
        'course': course,
        'is_major_badge': False,
        'is_active': True,
        'auto_approve_when_eligible': False,
    }
    return Badge.objects.create(**defaults)


def upsert_master_badge(courses):
    park_count = sum(1 for course in courses if course.course_type == Course.COURSE_TYPE_PARK_SPECIFIC)
    return Badge.objects.create(
        name='Certified Bako and Semenggoh Guide Badge',
        description='Awarded after completing the full final-phase general, Bako, and Semenggoh training catalog.',
        name_translations={
            'en': 'Certified Bako and Semenggoh Guide Badge',
            'ms': 'Lencana Panduan Bako dan Semenggoh Bertauliah',
            'zh': '巴哥与实蒙谷认证导览员徽章',
        },
        description_translations={
            'en': 'Awarded after completing the full final-phase general, Bako, and Semenggoh training catalog.',
            'ms': 'Dianugerahkan selepas melengkapkan katalog latihan umum, Bako, dan Semenggoh fasa akhir.',
            'zh': '完成最终阶段通用、巴哥和实蒙谷完整培训目录后获得。',
        },
        badge_image_url=TRAINING_IMAGE,
        badge_image_source=TRAINING_IMAGE,
        skills_awarded=['General guiding', 'Bako operations', 'Semenggoh operations', 'Integrated AR decisions'],
        lesson_highlights=[localized(course.title) for course in courses],
        required_completed_modules=0,
        required_badges_count=park_count + len(general_codes()),
        is_major_badge=True,
        is_active=True,
        auto_approve_when_eligible=True,
    )


class Command(BaseCommand):
    help = 'Replace the visible catalog with rich final-phase general, Bako, and Semenggoh courses plus badges.'

    def add_arguments(self, parser):
        parser.add_argument('--no-sync', action='store_true', help='Skip user badge row sync after seeding.')
        parser.add_argument('--keep-old', action='store_true', help='Keep old courses published instead of archiving them.')
        parser.add_argument('--delete-old', action='store_true', help='Hard-delete courses and course badges outside this final catalog.')

    @transaction.atomic
    def handle(self, *args, **options):
        ensure_seed_data()
        catalog = build_catalog()
        keep_codes = [item['code'] for item in catalog]
        deleted_old = None
        if options.get('delete_old'):
            deleted_old = delete_old_catalog(keep_codes)
        elif not options.get('keep_old'):
            archive_old_catalog(keep_codes)

        did_disconnect = post_save.disconnect(sync_badges_when_badge_changes, sender=Badge)
        try:
            target_badge_names = [f'{item["title"]} Badge' for item in catalog]
            target_badge_names.append('Certified Bako and Semenggoh Guide Badge')
            Badge.objects.filter(course__code__in=keep_codes).delete()
            Badge.objects.filter(name__in=target_badge_names).delete()
            Course.objects.filter(code__in=keep_codes).delete()

            courses = [upsert_course(item) for item in catalog]
            for course in courses:
                upsert_badge(course)
            upsert_master_badge(courses)

            sync_message = ' User badge sync skipped.'
            if not options.get('no_sync'):
                summary = sync_all_badges_for_all_users()
                sync_message = f' User badge rows created: {summary["created"]}.'

            self.stdout.write(
                self.style.SUCCESS(
                    f'Final training catalog ready. Published {len(courses)} courses '
                    f'({len(general_codes())} general, {len(courses) - len(general_codes())} park-specific).'
                    f'{sync_message}'
                    + (f' Deleted {deleted_old[0]} old course(s) and {deleted_old[1]} old badge(s).' if deleted_old else '')
                )
            )
        finally:
            if did_disconnect:
                post_save.connect(sync_badges_when_badge_changes, sender=Badge)
