from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Fieldset, Layout, Submit

from dal import autocomplete

from examiner.models import DocumentInfoSource, DocumentInfo, Pdf
from semesterpage.models import Course


class VerifyExamForm(forms.ModelForm):
    courses = forms.ModelMultipleChoiceField(
        label=_('Fag'),
        queryset=Course.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(
            url='semesterpage-course-autocomplete',
            attrs={
                'data-placeholder': _('Fagkode/fagnavn'),

                # Only trigger autocompletion after 3 characters have been typed
                'data-minimum-input-length': 3,
            },
        )
    )
    pdf = forms.ModelChoiceField(
        label=_('Pdf'),
        queryset=Pdf.objects.all(),
    )
    verifier = forms.ModelChoiceField(
        label=_('Bruker som verifiserer'),
        queryset=get_user_model().objects.all(),
    )

    class Meta:
        model = DocumentInfo
        exclude = ['course', 'course_code']
        labels = {
            'language': _('Språk'),
            'year': _('År'),
            'season': _('Semestertype'),
            'content_type': _('Dokumenttype'),
            'solutions': _('LF'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'verify-form'
        self.helper.form_method = 'post'
        self.helper.form_action = 'verify'

        self.helper.layout = Layout(
            Fieldset(
                _('PDF klassifisering'),
                Field(
                    'content_type',
                    onchange='onContentTypeChange()',
                ),
                'courses',
                'language',
                'year',
                'season',
                'solutions',
                'exercise_number',
                Field('pdf', type='hidden', readonly=True),
                Field('verifier', type='hidden', readonly=True),
            ),
            Submit(
                'verify',
                _('&check; Verifiser'),
                css_class='btn btn-success btn-block',
            ),
            Submit(
                'trash',
                _('✖ Slett'),
                css_class='btn btn-danger btn-block',
            ),
        )

        # Change semester type radio button labels
        self.fields['season'].choices = [
            (1, 'Vår'),
            (2, 'Kont'),
            (3, 'Høst'),
            (None, 'Ukjent'),
        ]

        # Set required fields
        self.fields['pdf'].required = True
        self.fields['verifier'].required = True

    def save(self, commit=True):
        # Only committing save is implemented ATM
        assert commit

        docinfo = self.instance
        data = self.cleaned_data

        courses = data.pop('courses')
        pdf = data.pop('pdf')
        verifier = data.pop('verifier')

        for course in courses:
            docinfo, _ = DocumentInfo.objects.get_or_create(
                course=course,
                course_code=course.course_code,
                **data,
            )
            exam_pdf, _ = DocumentInfoSource.objects.get_or_create(
                document_info=docinfo,
                pdf=pdf,
                verified_by__isnull=False,
            )
            exam_pdf.verified_by.add(verifier)
            exam_pdf.save()


class ExamsSearchForm(forms.ModelForm):
    courses = forms.ModelMultipleChoiceField(
        label=_('Fag'),
        queryset=Course.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(
            url='semesterpage-course-autocomplete',
            attrs={
                'data-placeholder': _('Fagkode/fagnavn'),

                # Only trigger autocompletion after 3 characters have been typed
                'data-minimum-input-length': 3,
            },
        )
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'verify-form'
        self.helper.form_method = 'post'
        self.helper.form_action = 'verify'

        self.helper.layout = Layout(
            Fieldset(
                _('PDF klassifisering'),
                'courses',
            ),
            Submit(
                'search',
                _('&check; Søk'),
                css_class='btn btn-success btn-block',
            ),
        )
        self.fields['pdf'].required = True
