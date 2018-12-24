from django.core.management.base import BaseCommand, CommandError

from examiner.crawlers import MathematicalSciencesCrawler
from examiner.models import Pdf, PdfUrl
from semesterpage.models import Course


class Command(BaseCommand):
    help = 'Crawl sources for exam PDFs.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--crawl',
            action='store_true',
            dest='crawl',
            help='Crawl PDF URLs from the internet.',
        )
        parser.add_argument(
            '--backup',
            action='store_true',
            dest='backup',
            help='Backup PDF files from the internet.',
        )
        parser.add_argument(
            '--parse',
            action='store_true',
            dest='parse',
            help='Read and parse content of PDF backups.',
        )
        parser.add_argument(
            'course_code',
            nargs='?',
            type=str,
            default='all',
            help='Restrict command to only one course.',
        )

    def handle(self, *args, **options):
        course_code = options['course_code'].upper()
        if options['crawl']:
            self.crawl(course_code=course_code)
        if options['backup']:
            self.backup(course_code=course_code)
        if options['parse']:
            self.parse()

    def crawl(self, course_code: str) -> None:
        """Crawl PDF links from the internet."""
        if course_code == 'ALL':
            courses = Course.objects.filter(course_code__startswith='TMA')
        else:
            course_code = course_code.upper()
            if 'TMA' != course_code[:3]:
                raise CommandError('Only TMA course codes are supported ATM.')
            courses = Course.objects.filter(course_code=course_code)

        self.stdout.write(f'Crawling courses: {courses}')
        new_urls = 0
        tma_crawlers = MathematicalSciencesCrawler(courses=courses)
        for crawler in tma_crawlers:
            self.stdout.write(self.style.SUCCESS(repr(crawler)))
            for url in crawler.pdf_urls():
                exam_url, new = PdfUrl.objects.get_or_create(url=url)
                exam_url.parse_url()
                self.stdout.write(f' * {repr(exam_url.exam)}\n   {url}')

                if new:
                    new_urls += 1

        self.stdout.write(self.style.SUCCESS(f'{new_urls} new URLs found!'))

    def backup(self, course_code: str) -> None:
        """Backup PDF URLs already scraped and saved in the database."""
        exam_urls = (
            PdfUrl.objects
            .filter(scraped_pdf__isnull=True)
            .exclude(dead_link=True)
        )
        if course_code != 'ALL':
            exam_urls = exam_urls.filter(
                exam__course_code__iexact=course_code,
            )

        new_backups = 0
        for exam_url in exam_urls:
            new = exam_url.backup_file()
            if new:
                new_backups += 1
                self.stdout.write('[NEW]', ending='')
            self.stdout.write(f'Backed up {repr(exam_url.exam)}')

        self.stdout.write(self.style.SUCCESS(
            f'{new_backups} new PDFs backed up!',
        ))

    def parse(self) -> None:
        """Read content of backed up PDF files."""
        new_content = 0
        for pdf in Pdf.objects.all():
            if pdf.pages.count() > 0:
                continue
            pdf.read_text()
            pdf.save()
            self.stdout.write(self.style.SUCCESS(
                f'Saved {pdf.pages.count()} new pages',
            ))
            new_content += 1

        self.stdout.write(self.style.SUCCESS(f'{new_content} new PDFs read!'))
