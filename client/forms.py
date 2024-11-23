import re
import os
import time
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
from django import forms
from django.core import validators
from django.db.models.base import Model
from .models import CategoryModel
from bootstrap_datepicker_plus.widgets import DatePickerInput

CONTACT_MESSAGE_TYPE_CHOICES = [
    (1, "Complaint"),
    (2, "Question"),
    (3, "Review"),
    (4, "Request"),
    (5, "Appointment")
]

class CategoryChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj: CategoryModel) -> str:
        return obj.name

class FilterProductsForm(forms.Form):
    name = forms.CharField(max_length=100, label="Name", required=False)
    categories = CategoryChoiceField(queryset=CategoryModel.objects.all(), required=False, empty_label="None")

def letters_and_spaces(value):
    if re.match(r'^[A-Z]+[a-zA-Z ]*$', value):
        return True
    else:
        raise forms.ValidationError("Field should start with a capital letter and only contain letters and spaces!")

class ContactForm(forms.Form):
    first_name = forms.CharField(required=True, max_length=10, label="First name", validators=[letters_and_spaces])
    last_name = forms.CharField(required=True, max_length=10, label="Last name", validators=[letters_and_spaces])
    birth_date = forms.DateField(required=False, label="Birth date", widget=DatePickerInput())
    email = forms.EmailField(required=True, label="Email")
    confirm_email = forms.EmailField(required=True, label="Confirm email")
    message_type = forms.ChoiceField(required=True, choices=CONTACT_MESSAGE_TYPE_CHOICES, label="Contact reason")
    subject = forms.CharField(required=True, max_length=100, label="Subject", validators=[letters_and_spaces])
    minimum_wait_time = forms.IntegerField(required=True, min_value=1, label="Urgency (in days)")
    message = forms.CharField(required=True, max_length=10000, label="Message", widget=forms.Textarea())
    
    def clean(self):
        cleaned_data = super().clean()
        
        message_type_name = ''
        for message_type in CONTACT_MESSAGE_TYPE_CHOICES:
            if message_type[0] == cleaned_data.get("message_type"):
                message_type_name = message_type[1]
                break
        
        data_to_save = {
            'Name': f"{cleaned_data.get('first_name')} {cleaned_data.get('last_name')}",
            'Email': cleaned_data.get("email"),
            'Message type': message_type_name,
            'Urgency': str(cleaned_data.get("minimum_wait_time")) + " days",
            'Subject': cleaned_data.get("subject"),
        }
        
        email = cleaned_data.get("email")
        confirm_email = cleaned_data.get("confirm_email")
        if email and confirm_email and email != confirm_email:
            raise forms.ValidationError("Email addresses are not the same!")
        
        birth_date = cleaned_data.get("birth_date")
        if birth_date:
            relative_date = relativedelta(datetime.now(), birth_date)
            if (relative_date.years) < 18:
                raise forms.ValidationError("You must be over 18 years of age to submit a contact request!")
            data_to_save['Age'] = f"{relative_date.years} years, {relative_date.months} months"
            
        message = cleaned_data.get("message")
        last_name = cleaned_data.get("last_name")
        message_split = re.findall(r'\w+', message)
        if not (5 <= len(message_split) <= 100):
            raise forms.ValidationError("Message should contain between 5 and 100 words!")
        if message.find("http://") != -1 or message.find("https://") != -1:
            raise forms.ValidationError("Message should not contain any links!")
        if message_split[-1] != last_name:
            raise forms.ValidationError("Message should contain your signature at the end!")
        
        message.replace("\n", " ")
        message.replace("\r", " ")
        cleaned_message = re.sub(r" {2,}", ' ', message)
        data_to_save['Message'] = cleaned_message
        
        timestamp = int(time.time())
        current_dir = os.path.dirname(__file__)
        messages_dir = os.path.join(current_dir, '../messages')
        with open(f"{messages_dir}/message_{timestamp}.json", "w+") as file:
            json.dump(data_to_save, file)
        