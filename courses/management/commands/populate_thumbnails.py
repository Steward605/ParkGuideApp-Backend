from django.core.management.base import BaseCommand
from courses.models import Course

class Command(BaseCommand):
    help = 'Populate thumbnail URLs for all courses'

    def handle(self, *args, **options):
        thumbnails = {
            'park-guide-101': 'https://images.pexels.com/photos/1366919/pexels-photo-1366919.jpeg?auto=compress&cs=tinysrgb&w=600',
            'park-guide-201': 'https://images.pexels.com/photos/2398220/pexels-photo-2398220.jpeg?auto=compress&cs=tinysrgb&w=600',
            'park-guide-301': 'https://images.pexels.com/photos/3694820/pexels-photo-3694820.jpeg?auto=compress&cs=tinysrgb&w=600',
            'park-guide-401': 'https://images.pexels.com/photos/3957984/pexels-photo-3957984.jpeg?auto=compress&cs=tinysrgb&w=600',
            'park-guide-501': 'https://images.pexels.com/photos/3807517/pexels-photo-3807517.jpeg?auto=compress&cs=tinysrgb&w=600',
        }

        for course in Course.objects.all():
            if course.code in thumbnails:
                course.thumbnail = thumbnails[course.code]
                course.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Updated {course.code} with thumbnail'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠ No thumbnail for {course.code}'
                    )
                )

        self.stdout.write(self.style.SUCCESS('Thumbnail population complete!'))
