from django import forms
from django.forms import ModelForm

from .models import Recipe


class RecipeCreateForm(ModelForm):

    cooking_time = forms.IntegerField(required=True)

    class Meta:
        model = Recipe
        fields = ('title', 'tags', 'cooking_time', 'description', 'image',)
        widgets = {
            'tags': forms.CheckboxSelectMultiple(),
        }


class RecipeForm(ModelForm):

    cooking_time = forms.IntegerField(required=True)

    class Meta:
        model = Recipe
        fields = ('title', 'cooking_time', 'description', 'image',)
