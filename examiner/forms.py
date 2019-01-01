from django import forms
from django.utils.translation import ugettext_lazy as _

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset, Layout, Submit
from crispy_forms.bootstrap import InlineRadios

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
                'courses',
                'language',
                'year',
                'season',
                'solutions',
            ),
            Submit(
                'verify',
                _('&check; Verifiser'),
                css_class='btn btn-success btn-block',
            ),
            Submit(
                'exercise',
                _('Øving'),
                css_class='btn btn-primary btn-block',
            ),
            Submit(
                'trash',
                _('✖ Slett'),
                css_class='btn btn-danger btn-block',
            ),
        )
        # Use semester type radio buttons instead of dropdown
        self.helper['season'].wrap(InlineRadios)

        # Change semester type radio button labels
        self.fields['season'].choices = [
            (1, 'Vår'),
            (2, 'Kont'),
            (3, 'Vår'),
            (None, 'Ukjent'),
        ]
