from django import forms
from semesterpage.models import CourseLink, Course


class LinkForm(forms.ModelForm):
    description = forms.CharField(max_length=300,
                                  widget=forms.Textarea,
                                  required=False)

    class Meta:
        model = CourseLink
        fields = ['title', 'url', 'category', 'course']


class FileForm(forms.Form):
    title = forms.CharField(max_length=60, required=False)
    course = forms.ModelChoiceField(queryset=Course.objects.all())
    user_files = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
    description = forms.CharField(max_length=300,
                                  widget=forms.Textarea,
                                  required=False)
