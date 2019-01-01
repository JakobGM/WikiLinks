from django import forms
from django.utils.translation import ugettext_lazy as _

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Fieldset, Layout, Submit

from dal import autocomplete

from examiner.models import DocumentInfo
from semesterpage.models import Course


class VerifyExamForm(forms.ModelForm):
    """
    Filler.
    """

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
