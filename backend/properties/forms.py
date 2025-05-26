from django import forms
from .models import Property
from mapwidgets import  LeafletPointFieldWidget, GoogleMapPointFieldWidget


class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = "__all__"
        widgets = {
            'location': GoogleMapPointFieldWidget(
                attrs={
                    'style': 'width: 100%; height: 400px;',
                    'map_options': {
                        'zoom': 15,
                        'center': {'lat': 0, 'lng': 0},
                    },
                }
            ),
        }