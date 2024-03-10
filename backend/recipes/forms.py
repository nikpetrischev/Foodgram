# Django Library
from django import forms
from django.forms.models import BaseInlineFormSet
from django.forms.widgets import TextInput

# Local Imports
from .models import Tag


class AtLeastOneRequiredInlineFormSet(BaseInlineFormSet):
    """
    Custom formset that requires at least one form to be filled out.

    This formset ensures that at least one instance of the related model is
    created or updated, which is useful for scenarios where you want to ensure
    that at least one related object is present.
    """

    def clean(self) -> None:
        """
        Validate the formset.

        This method overrides the default clean method to ensure that at least
        one form in the formset is filled out. If no forms are filled out, it
        raises a ValidationError.
        """
        super(AtLeastOneRequiredInlineFormSet, self).clean()
        if any(self.errors):
            return
        if not any(
                cleaned_data and not cleaned_data.get('DELETE', False)
                for cleaned_data in self.cleaned_data
        ):
            raise forms.ValidationError('Заполните хотя бы одно значение')


class TagAdminForm(forms.ModelForm):
    """
    Model form for the Tag model.

    This form includes a custom widget for the color field to allow users to
    select a color using a color picker.
    """

    class Meta:
        model = Tag
        fields = ('name', 'slug', 'color')
        widgets = {
            'color': TextInput(attrs={'type': 'color'}),
        }
