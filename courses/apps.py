from django.apps import AppConfig


class CoursesConfig(AppConfig):
    name = 'courses'
    
    def ready(self):
        """Register signals when app is ready"""
        import courses.signals  # noqa
        import courses.progress_signals  # noqa
