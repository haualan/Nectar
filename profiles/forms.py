from django import forms
import datetime

class SettingsForm(forms.Form):
    name = forms.CharField(label='Your name / Avatar', max_length=100)
    birth_date = forms.DateField(label='Birth Date', required=False, initial=datetime.date.today)
    



# from django import forms

# class NameForm(forms.Form):
#     your_name = forms.CharField(label='Your name', max_length=100)