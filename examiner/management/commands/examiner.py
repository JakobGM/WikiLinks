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
            '--classify',
            action='store_true',
            dest='classify',
            help='Read and classify content of PDF backups.',
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
        if options['classify']:
            if not OCR_ENABLED:
                raise CommandError('OCR dependencies not properly installed!')
            self.classify()
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
                exam_url.classify()
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

    def classify(self) -> None:
        """Read content of backed up PDF files and classify content."""
        successes = 0
        errors = 0
        for pdf in Pdf.objects.all():
            classify_success = pdf.classify(
                read=True,
                allow_ocr=True,
                save=True,
            )
            if not classify_success:
                errors += 1
                self.stdout.write(self.style.ERROR(f'PDF classify error!'))
                continue

            self.stdout.write(self.style.SUCCESS(
                f'Saved {pdf.pages.count()} new pages. Exam: {repr(pdf.exam)}',
            ))
            successes += 1

        self.stdout.write(self.style.SUCCESS(f'{successes} new PDFs read!'))
        if errors:
            self.stdout.write(self.style.ERROR(f'{errors} errors!'))

    def test(self, gui: bool = False) -> None:
        pdfs = Pdf.objects.all()
        for pdf in pdfs:
            self.stdout.write(self.style.SUCCESS(repr(pdf)))
            self.stdout.write('Hosted at:')
            for pdf_url in pdf.hosted_at.all():
                self.stdout.write(' - ' + pdf_url.url)

            first_page = pdf.pages.first()
            self.stdout.write('-' * 35 + 'FIRST PAGE' + '-' * 35)
            self.stdout.write(first_page.text)
            self.stdout.write('-' * 80)

            parser = PdfParser(text=pdf.pages.first().text)
            self.stdout.write(repr(parser))

            exam_not_determined = (
                parser.language is None or
                parser.season is None or
                parser.year is None or
                not parser.course_codes
            )
            if exam_not_determined and (first_page.confidence or 100) > 60:
                # self.stdout.write(pdf.text)
                self.stdout.write(
                    self.style.ERROR('Could not exam type!'),
                )
                self.stdout.write(f'Page confidence: {first_page.confidence}')
                self.stdout.write('Hosted at: ' + pdf.hosted_at.first().url)
                answer = input('[r] Reparse, [o] Force OCR: ')
                if answer == 'r':
                    url = pdf.hosted_at.first()
                    pdf.delete()
                    url.backup_file()
                    pdf = url.scraped_pdf
                    pdf.read_text(allow_ocr=True)
                    continue
                if answer == 'o':
                    pdf.pages.all().delete()
                    pdf.read_text(force_ocr=True)
                    continue
            self.stdout.write('\n')
