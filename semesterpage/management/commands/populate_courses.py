from django.core.management.base import BaseCommand

import requests

from tqdm import tqdm

from semesterpage.models import Course


class Command(BaseCommand):
    help = 'Populate Course objects from NTNU-IME API.'

    def handle(self, *args, **options):
        existing_courses = set(
            Course
            .objects
            .all()
            .values_list('course_code', flat=True)
        )

        new_courses = 0

        api = IMEAPI()
        try:
            for course in tqdm(api.all_courses()):
                if course['course_code'] in existing_courses:
                    tqdm.write('[ALREADY EXISTS] ' + str(course))
                    continue
                Course.objects.create(**course)
                tqdm.write('[NEW COURSE] ' + str(course))
                new_courses += 1
        except KeyboardInterrupt:
            pass

        self.stdout.write(
            self.style.SUCCESS(f'{new_courses} new Course objects created'),
        )


class IMEAPI:
    """Class for interacting with the NTNU-IME API."""

    COURSE_URL = 'https://www.ime.ntnu.no/api/course/'

    @classmethod
    def all_courses(cls):
        """Yield all courses available from the IME API."""
        response = requests.get(cls.COURSE_URL + '-')
        courses = response.json()['course']
        for course in courses:
            course_code = course['code']
            response = requests.get(cls.COURSE_URL + course_code)
            course_info = response.json()['course']

            yield {
                'course_code': course_code.upper(),
                'full_name': course_info['name'],
                'homepage': cls.course_homepage(course_info),
            }

    @staticmethod
    def course_homepage(course):
        """Retrieve course homepage if present in Course API response."""
        info_types = course.get('infoType')
        if not info_types:
            return ''

        for info in info_types:
            if info['code'] == 'E-URL' and 'text' in info:
                return info['text'] or ''

        return ''
