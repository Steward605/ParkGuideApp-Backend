import json
from functools import lru_cache
from pathlib import Path

from courses.models import Course


@lru_cache(maxsize=1)
def _load_prerequisite_map():
    """Load course prerequisite codes from local JSON seed files."""
    data_dir = Path(__file__).resolve().parent / 'data'
    files = ['courses_complete.json', 'courses_stress_test.json']
    prerequisite_map = {}

    for filename in files:
        path = data_dir / filename
        if not path.exists():
            continue

        with path.open('r', encoding='utf-8') as handle:
            courses_data = json.load(handle)

        if not isinstance(courses_data, list):
            courses_data = [courses_data]

        for item in courses_data:
            code = item.get('code')
            if not code:
                continue
            prerequisite_map[code] = item.get('prerequisites', [])

    return prerequisite_map


def get_effective_prerequisite_codes(course):
    """Return prerequisite codes from DB, or fall back to local JSON definitions."""
    db_codes = list(course.prerequisites.values_list('code', flat=True).order_by('code'))
    if db_codes:
        return db_codes
    return _load_prerequisite_map().get(course.code, [])


def get_effective_prerequisite_courses(course):
    """Return prerequisite course queryset/list with JSON fallback."""
    db_courses = list(course.prerequisites.all().order_by('code'))
    if db_courses:
        return db_courses

    codes = get_effective_prerequisite_codes(course)
    if not codes:
        return []

    courses_by_code = {
        item.code: item
        for item in Course.objects.filter(code__in=codes)
    }
    return [courses_by_code[code] for code in codes if code in courses_by_code]
