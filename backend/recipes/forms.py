# Django Library
from django import forms
from django.forms.models import BaseInlineFormSet
from django.forms.widgets import TextInput

# Local Imports
from .models import Tag


class AtLeastOneRequiredInlineFormSet(BaseInlineFormSet):

    def clean(self):
        super(AtLeastOneRequiredInlineFormSet, self).clean()
        if any(self.errors):
            return
        if not any(
                cleaned_data and not cleaned_data.get('DELETE', False)
                for cleaned_data in self.cleaned_data
        ):
            raise forms.ValidationError('Заполните хотя бы одно значение')


class TagAdminForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ('name', 'slug', 'color')
        widgets = {
            'color': TextInput(attrs={'type': 'color'}),
        }
