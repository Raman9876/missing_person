from django import forms
from .models import MissingPerson

class MissingPersonForm(forms.ModelForm):
    class Meta:
        model = MissingPerson
        fields = ['name', 'age','additional_audio','last_seen_location','latitude', 'longitude', 'photo', 'parent_email', 'parent_phone']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent_email'].required = True  # Ensure users must enter an email