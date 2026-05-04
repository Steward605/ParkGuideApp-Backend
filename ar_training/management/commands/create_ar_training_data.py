"""
Seed immersive AR/VR park-guide training simulations.

Usage:
    python manage.py create_ar_training_data
"""
from django.core.management.base import BaseCommand

from ar_training.models import (
    AR360Panorama,
    ARBadge,
    ARInteractiveHotspot,
    ARScenarioSequence,
    ARSimulationQuiz,
    ARSimulationScenario,
)


FIREBASE_FOREST = (
    "https://firebasestorage.googleapis.com/v0/b/parkguideapp-c8517.firebasestorage.app/"
    "o/assests%2F360%2FAdobeStock_15550322.jpeg?alt=media&token=c9d64eed-c48a-4075-b9e3-35314566cd68"
)


def ml(en, ms, zh):
    return {"en": en, "ms": ms, "zh": zh}


SCENARIOS = [
    {
        "code": "ar-biodiversity-guide-sim",
        "scenario_type": "biodiversity",
        "difficulty": "intermediate",
        "order": 1,
        "duration_minutes": 12,
        "immersion_type": "guided_tour",
        "park_location": "Tropical rainforest trail",
        "weather_best": "Morning or shaded afternoon",
        "title": ml("Forest Biodiversity Guiding Simulation", "Simulasi Panduan Biodiversiti Hutan", "森林生物多样性导览模拟"),
        "description": ml(
            "Practise introducing visitors to forest layers, species relationships, microhabitats, and low-impact observation.",
            "Latih cara memperkenalkan lapisan hutan, hubungan spesies, mikrohabitat, dan pemerhatian rendah impak kepada pelawat.",
            "练习向游客介绍森林层次、物种关系、微栖息地和低影响观察方式。",
        ),
        "objectives": [
            ml("Explain biodiversity using visible forest evidence.", "Terangkan biodiversiti menggunakan bukti hutan yang dapat dilihat.", "用可见的森林证据解释生物多样性。"),
            ml("Connect guide narration to visitor safety and trail etiquette.", "Hubungkan penerangan pemandu dengan keselamatan pelawat dan etika laluan.", "把导览讲解与游客安全和步道礼仪联系起来。"),
        ],
        "hotspots": [
            ("canopy_layer", 38, 34, "tree", "#2E7D32", ml("Canopy Layer", "Lapisan Kanopi", "林冠层"), ml("Show how the canopy regulates light, shelter, and food for birds and insects.", "Tunjukkan bagaimana kanopi mengawal cahaya, perlindungan, dan makanan untuk burung serta serangga.", "说明林冠如何调节光照，并为鸟类和昆虫提供庇护与食物。")),
            ("understory_plants", 128, 8, "sprout", "#43A047", ml("Understory Plants", "Tumbuhan Lapisan Bawah", "林下植物"), ml("Point out shade-tolerant plants and remind visitors to stay on the trail.", "Tunjukkan tumbuhan tahan teduh dan ingatkan pelawat supaya kekal di laluan.", "指出耐阴植物，并提醒游客留在步道上。")),
            ("forest_floor", 210, -24, "mushroom", "#795548", ml("Forest Floor", "Lantai Hutan", "森林地面"), ml("Use leaf litter and fungi to explain nutrient cycling and decomposition.", "Gunakan daun reput dan kulat untuk menerangkan kitaran nutrien dan pereputan.", "利用落叶和真菌解释养分循环与分解。")),
            ("pollinator_microhabitat", 292, 14, "bee", "#F9A825", ml("Pollinator Microhabitat", "Mikrohabitat Pendebunga", "传粉者微栖息地"), ml("Explain why flowers, insects, and small animals are part of one shared system.", "Terangkan mengapa bunga, serangga, dan haiwan kecil berada dalam satu sistem bersama.", "说明花、昆虫和小动物为什么属于同一个生态系统。")),
        ],
        "quiz": (
            ml("A visitor asks why fallen logs should not be removed. What is the strongest guide response?", "Pelawat bertanya mengapa kayu tumbang tidak patut dialihkan. Apakah jawapan pemandu terbaik?", "游客问为什么不应移走倒木。最佳导游回答是什么？"),
            {
                "en": ["They recycle nutrients and shelter organisms.", "They make the trail look natural only.", "They are usually owned by the park office.", "They stop all animals from entering the trail."],
                "ms": ["Ia mengitar nutrien dan melindungi organisma.", "Ia hanya membuat laluan nampak semula jadi.", "Ia biasanya dimiliki pejabat taman.", "Ia menghalang semua haiwan masuk ke laluan."],
                "zh": ["它们循环养分并庇护生物。", "它们只是让步道看起来自然。", "它们通常属于公园办公室。", "它们阻止所有动物进入步道。"],
            },
            0,
        ),
    },
    {
        "code": "ar-ecotourism-practice-sim",
        "scenario_type": "ecotourism",
        "difficulty": "beginner",
        "order": 2,
        "duration_minutes": 10,
        "immersion_type": "simulation",
        "park_location": "Visitor trail and rest stop",
        "weather_best": "Any open park day",
        "title": ml("Eco-tourism Visitor Management Simulation", "Simulasi Pengurusan Pelawat Eko-pelancongan", "生态旅游游客管理模拟"),
        "description": ml(
            "Practise group control, low-impact behaviour, photo-stop management, and community-positive interpretation.",
            "Latih kawalan kumpulan, tingkah laku rendah impak, pengurusan tempat bergambar, dan interpretasi yang menyokong komuniti.",
            "练习团队管理、低影响行为、拍照点管理和支持社区的讲解。",
        ),
        "objectives": [
            ml("Reduce visitor impact while keeping the tour welcoming.", "Kurangkan impak pelawat sambil mengekalkan lawatan yang mesra.", "在保持友好体验的同时降低游客影响。"),
            ml("Use short, confident instructions in crowded trail moments.", "Gunakan arahan ringkas dan yakin ketika laluan sesak.", "在步道拥挤时使用简短自信的指令。"),
        ],
        "hotspots": [
            ("trail_boundary", 22, -16, "walk", "#00897B", ml("Trail Boundary", "Sempadan Laluan", "步道边界"), ml("Ask the group to stay on durable surfaces and explain seedling protection.", "Minta kumpulan kekal di permukaan tahan lasak dan terangkan perlindungan anak pokok.", "请团队停留在耐踩踏区域，并解释幼苗保护。")),
            ("photo_stop", 118, 0, "camera", "#039BE5", ml("Safe Photo Stop", "Tempat Bergambar Selamat", "安全拍照点"), ml("Move visitors to a safe photo point without blocking other walkers.", "Alihkan pelawat ke tempat bergambar selamat tanpa menghalang pejalan lain.", "引导游客到安全拍照点，避免阻塞其他行人。")),
            ("waste_check", 246, -30, "trash-can-outline", "#7CB342", ml("Leave No Trace Check", "Semakan Tidak Tinggal Kesan", "无痕检查"), ml("Prompt visitors to carry out waste and avoid collecting natural objects.", "Ingatkan pelawat membawa keluar sampah dan tidak mengambil objek semula jadi.", "提醒游客带走垃圾，不采集自然物。")),
        ],
        "quiz": (
            ml("A group blocks the trail for photos. What should the guide do first?", "Kumpulan menghalang laluan untuk bergambar. Apakah tindakan pertama pemandu?", "团队为了拍照挡住步道。导游第一步应做什么？"),
            {
                "en": ["Politely move them to a safe photo stop.", "Cancel the tour immediately.", "Tell other visitors to wait silently.", "Let them continue because photos are harmless."],
                "ms": ["Dengan sopan bawa mereka ke tempat bergambar selamat.", "Batalkan lawatan serta-merta.", "Suruh pelawat lain menunggu senyap.", "Biarkan kerana bergambar tidak berbahaya."],
                "zh": ["礼貌地引导他们到安全拍照点。", "立即取消行程。", "让其他游客安静等待。", "让他们继续，因为拍照无害。"],
            },
            0,
        ),
    },
    {
        "code": "ar-wildlife-encounter-sim",
        "scenario_type": "wildlife",
        "difficulty": "advanced",
        "order": 3,
        "duration_minutes": 14,
        "immersion_type": "simulation",
        "park_location": "Wildlife observation trail",
        "weather_best": "Guide-supervised daylight",
        "title": ml("Wildlife Encounter Response Simulation", "Simulasi Respons Pertemuan Hidupan Liar", "野生动物遭遇应对模拟"),
        "description": ml(
            "Practise calm visitor control, safe distance, no-feeding messaging, rerouting, and emergency escalation.",
            "Latih kawalan pelawat secara tenang, jarak selamat, mesej jangan beri makan, tukar laluan, dan eskalasi kecemasan.",
            "练习冷静控团、安全距离、禁止喂食、改道和紧急升级处理。",
        ),
        "objectives": [
            ml("Identify risky encounter cues before visitors panic.", "Kenal pasti petunjuk pertemuan berisiko sebelum pelawat panik.", "在游客恐慌前识别危险遭遇信号。"),
            ml("Choose safe guide actions during a blocked trail.", "Pilih tindakan pemandu yang selamat apabila laluan terhalang.", "在步道受阻时选择安全导游行动。"),
        ],
        "hotspots": [
            ("safe_distance", 54, 4, "shield-check", "#D32F2F", ml("Safe Distance", "Jarak Selamat", "安全距离"), ml("Stop the group calmly, lower noise, and increase distance without sudden movement.", "Hentikan kumpulan dengan tenang, kurangkan bunyi, dan tambah jarak tanpa gerakan mengejut.", "冷静停止团队，降低音量，并在不突然移动的情况下拉开距离。")),
            ("no_feeding", 150, 18, "food-off", "#F4511E", ml("No Feeding", "Jangan Beri Makan", "禁止喂食"), ml("Explain that feeding changes wildlife behaviour and creates future danger.", "Terangkan bahawa memberi makan mengubah tingkah laku hidupan liar dan mewujudkan bahaya masa depan.", "说明喂食会改变野生动物行为并造成未来风险。")),
            ("reroute_decision", 236, -10, "directions-fork", "#5E35B1", ml("Reroute Decision", "Keputusan Tukar Laluan", "改道决策"), ml("Use an approved alternative route or wait until the area is clear.", "Gunakan laluan alternatif diluluskan atau tunggu sehingga kawasan selamat.", "使用批准的替代路线，或等待区域安全。")),
            ("emergency_signal", 318, -22, "radio-handheld", "#C62828", ml("Emergency Signal", "Isyarat Kecemasan", "紧急信号"), ml("Escalate if wildlife approaches, visitors are injured, or the group cannot retreat safely.", "Eskalasi jika hidupan liar menghampiri, pelawat cedera, atau kumpulan tidak dapat berundur dengan selamat.", "如果野生动物靠近、游客受伤或团队无法安全撤离，应立即升级处理。")),
        ],
        "quiz": (
            ml("Wildlife blocks the trail ahead. What is the safest guide action?", "Hidupan liar menghalang laluan di hadapan. Apakah tindakan pemandu paling selamat?", "野生动物挡住前方步道。最安全的导游行动是什么？"),
            {
                "en": ["Stop, keep distance, and reroute or wait.", "Walk closer for a better look.", "Feed it so it moves away.", "Ask visitors to run past quickly."],
                "ms": ["Berhenti, kekalkan jarak, dan tukar laluan atau tunggu.", "Dekati untuk melihat lebih jelas.", "Beri makan supaya ia pergi.", "Minta pelawat berlari cepat melintas."],
                "zh": ["停止、保持距离，并改道或等待。", "靠近以看得更清楚。", "喂食让它离开。", "让游客快速跑过去。"],
            },
            0,
        ),
    },
]


class Command(BaseCommand):
    help = "Create or refresh AR training simulations"

    def handle(self, *args, **options):
        self.stdout.write("Refreshing AR training simulations...")

        ARSimulationScenario.objects.filter(code__in=[item["code"] for item in SCENARIOS]).delete()

        for item in SCENARIOS:
            scenario = ARSimulationScenario.objects.create(
                code=item["code"],
                title=item["title"],
                description=item["description"],
                learning_objectives=item["objectives"],
                scenario_type=item["scenario_type"],
                difficulty=item["difficulty"],
                duration_minutes=item["duration_minutes"],
                thumbnail=FIREBASE_FOREST,
                immersion_type=item["immersion_type"],
                initial_panorama_url=FIREBASE_FOREST,
                park_location=item["park_location"],
                weather_best=item["weather_best"],
                safety_warning=ml(
                    "Use the simulation for training only. Follow official park protocols in real encounters.",
                    "Gunakan simulasi untuk latihan sahaja. Ikut protokol rasmi taman dalam situasi sebenar.",
                    "该模拟仅用于培训。真实情况请遵守公园官方规程。",
                ),
                is_published=True,
                order=item["order"],
            )

            panorama = AR360Panorama.objects.create(
                scenario=scenario,
                name=f"{item['title']['en']} View",
                description=item["description"],
                panorama_url=FIREBASE_FOREST,
                thumbnail_url=FIREBASE_FOREST,
                initial_yaw=0,
                initial_pitch=0,
                order=1,
                is_key_view=True,
            )

            ARScenarioSequence.objects.create(
                scenario=scenario,
                step_number=1,
                panorama=panorama,
                narration_text=item["description"],
                recommended_time_seconds=120,
            )

            for order, (hotspot_id, yaw, pitch, icon, color, title, description) in enumerate(item["hotspots"], start=1):
                ARInteractiveHotspot.objects.create(
                    scenario=scenario,
                    panorama=panorama,
                    hotspot_id=hotspot_id,
                    title=title,
                    position_yaw=yaw,
                    position_pitch=pitch,
                    interaction_type="decision_point" if "sim" in scenario.code else "info_card",
                    content={
                        "description": description,
                        "guide_script": description,
                        "visitor_prompt": ml(
                            "How would you explain this clearly to visitors?",
                            "Bagaimana anda menerangkan perkara ini dengan jelas kepada pelawat?",
                            "你会如何向游客清楚说明这一点？",
                        ),
                    },
                    color_hint=color,
                    icon_type=icon,
                    order=order,
                    required_visit=True,
                )

            question, options, correct = item["quiz"]
            ARSimulationQuiz.objects.create(
                scenario=scenario,
                question_id=f"{scenario.code}-q1",
                question_text=question,
                options=options,
                correct_option_index=correct,
                correct_explanation=ml(
                    "Correct. This response protects visitors while supporting conservation goals.",
                    "Betul. Respons ini melindungi pelawat sambil menyokong matlamat pemuliharaan.",
                    "正确。这个回应保护游客，同时支持保护目标。",
                ),
                incorrect_explanation=ml(
                    "Review the hotspot guidance and choose the action that lowers risk and environmental impact.",
                    "Semak panduan hotspot dan pilih tindakan yang mengurangkan risiko serta impak alam sekitar.",
                    "请复习热点指导，并选择能降低风险和环境影响的行动。",
                ),
                difficulty_level="medium",
                time_limit_seconds=45,
                order=1,
            )

        badges = [
            ("ar_first_sim", ml("First AR Simulation", "Simulasi AR Pertama", "首次AR模拟"), ml("Complete one AR training simulation.", "Lengkapkan satu simulasi latihan AR.", "完成一个AR训练模拟。"), "Complete one AR scenario"),
            ("ar_field_ready", ml("Field Ready Guide", "Pemandu Sedia Lapangan", "实地准备导游"), ml("Complete biodiversity, eco-tourism, and wildlife simulations.", "Lengkapkan simulasi biodiversiti, eko-pelancongan, dan hidupan liar.", "完成生物多样性、生态旅游和野生动物模拟。"), "Complete all core AR scenarios"),
        ]
        for badge_id, name, description, requirement in badges:
            ARBadge.objects.update_or_create(
                badge_id=badge_id,
                defaults={
                    "name": name,
                    "description": description,
                    "icon_url": FIREBASE_FOREST,
                    "requirement": requirement,
                },
            )

        self.stdout.write(self.style.SUCCESS(f"Created {len(SCENARIOS)} AR simulations with panoramas, hotspots, and quizzes."))
