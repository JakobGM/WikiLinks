from django.core.management.base import BaseCommand, CommandError

from examiner.crawlers import MathematicalSciencesCrawler
from examiner.models import Pdf, PdfUrl
from examiner.parsers import PdfParser
from examiner.pdf import OCR_ENABLED
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
            '--test',
            action='store_true',
            dest='test',
            help='Run examiner interactive tests.',
        )
        parser.add_argument(
            '--gui',
            action='store_true',
            dest='gui',
            help='If GUI tools can be invoked by the command.',
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
            if not OCR_ENABLED:
                raise CommandError('OCR dependencies not properly installed!')
            self.backup(course_code=course_code)
        if options['parse']:
            if not OCR_ENABLED:
                raise CommandError('OCR dependencies not properly installed!')
            self.parse()
        if options['test']:
            self.test(gui=options['gui'])

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
            pdf.read_text(allow_ocr=True)
            pdf.save()
            self.stdout.write(self.style.SUCCESS(
                f'Saved {pdf.pages.count()} new pages',
            ))
            new_content += 1

        self.stdout.write(self.style.SUCCESS(f'{new_content} new PDFs read!'))

    def test(self, gui: bool = False) -> None:
        pdfs = Pdf.objects.all()
        for pdf in pdfs:
            self.stdout.write(self.style.SUCCESS(repr(pdf)))
            self.stdout.write('Hosted at:')
            for pdf_url in pdf.hosted_at.all():
                self.stdout.write(' - ' + pdf_url.url)

            self.stdout.write('-' * 35 + 'FIRST PAGE' + '-' * 35)
            self.stdout.write(pdf.pages.first().text)
            self.stdout.write('-' * 80)

            parser = PdfParser(text=pdf.pages.first().text)
            if parser.language is None:
                self.stdout.write(pdf.text)
                self.stdout.write(
                    self.style.ERROR('Could not determine language!'),
                )
                self.stdout.write('Hosted at: ' + pdf.hosted_at.first().url)
                input()
            self.stdout.write('\n')
