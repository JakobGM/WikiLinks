from django import forms
from django.utils.translation import ugettext_lazy as _

from dal import autocomplete

from .models import Course, Options

class OptionsForm(forms.ModelForm):
    """
    A form solely used for autocompleting Courses in the admin,
    using django-autocomplete-light,
    """

    self_chosen_courses = forms.ModelMultipleChoiceField(
        label=_('Dine fag'),
        queryset=Course.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(
            url='semesterpage-course-autocomplete',
            attrs = {
                'data-placeholder': _('Tast inn fagkode eller fagnavn'),

                # Only trigger autocompletion after 3 characters have been typed
                'data-minimum-input-length': 3,
            },
        )
    )

    class Meta:
        model = Options

        # The fields are further restricted in .admin.py
        fields = ('__all__')
