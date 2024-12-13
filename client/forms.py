import re
import os
import time
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
from django import forms
from django.core.validators import RegexValidator
from .models import CategoryModel, UnitModel, ProductModel, ProfileModel
from bootstrap_datepicker_plus.widgets import DatePickerInput
from django_select2 import forms as select2
from django_prose_editor.fields import ProseEditorFormField
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm, PasswordChangeForm
from cities_light.models import Country, City

# Custom select options

CONTACT_MESSAGE_TYPE_CHOICES = [
    (1, "Complaint"),
    (2, "Question"),
    (3, "Review"),
    (4, "Request"),
    (5, "Appointment")
]

PAGINATION_CHOICES = [(5, "5"), (10, "10"), (25, "25")]

# Custom fields


class CategoryChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj: CategoryModel) -> str:
        return obj.name


class UnitChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj: UnitModel) -> str:
        return obj.name

# Custom widgets


class CategoryMultipleChoiceWidget(select2.ModelSelect2MultipleWidget):
    queryset = CategoryModel.objects.all()
    search_fields = [
        "name__icontains"
    ]

    def label_from_instance(self, obj):
        return obj.name


class CountryChoiceWidget(select2.ModelSelect2Widget):
    queryset = Country.objects.all()
    empty_label = ''
    search_fields = [
        "name__icontains"
    ]

    def label_from_instance(self, obj):
        return obj.name


class CityChoiceWidget(select2.ModelSelect2Widget):
    queryset = City.objects.all()
    empty_label = ''
    search_fields = [
        "name__icontains"
    ]

    def label_from_instance(self, obj):
        return obj.name

# Custom validators


starts_with_capital_letter = RegexValidator(r'^[A-Z]', "Field should start with a capital letter")
letters_and_spaces = RegexValidator(r'^[a-zA-Z ]*$', "Field should only contain letters and spaces!")
unit_string = RegexValidator(r'^\d+(.\d+)?\ +[a-zA-Z]+$', "Unit should be of format \"Number UnitShortName\"!")
username = RegexValidator(r'^[A-Za-z][A-Za-z0-9_.]{6,30}$', "Username should have between 6 and 30 characters, and contain only lowercase and uppercase letters, numbers, dots and underscores.")

# Forms


class ContactForm(forms.Form):
    first_name = forms.CharField(required=True, max_length=10, label="First name", validators=[
                                 starts_with_capital_letter, letters_and_spaces])
    last_name = forms.CharField(required=True, max_length=10, label="Last name", validators=[
                                starts_with_capital_letter, letters_and_spaces])
    birth_date = forms.DateField(
        required=False, label="Birth date", widget=DatePickerInput())
    email = forms.EmailField(required=True, label="Email")
    confirm_email = forms.EmailField(required=True, label="Confirm email")
    message_type = forms.ChoiceField(
        required=True, choices=CONTACT_MESSAGE_TYPE_CHOICES, label="Contact reason")
    subject = forms.CharField(required=True, max_length=100, label="Subject", validators=[
                              starts_with_capital_letter, letters_and_spaces])
    minimum_wait_time = forms.IntegerField(
        required=True, min_value=1, label="Urgency (in days)")
    message = forms.CharField(
        required=True, max_length=10000, label="Message", widget=forms.Textarea())

    def clean(self):
        cleaned_data = super().clean()
        errors = []

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
            errors.append("Email addresses are not the same!")

        birth_date = cleaned_data.get("birth_date")
        if birth_date:
            relative_date = relativedelta(datetime.now(), birth_date)
            if (relative_date.years) < 18:
                errors.append(
                    "You must be over 18 years of age to submit a contact request!")
            data_to_save['Age'] = f"{relative_date.years} years, {relative_date.months} months"

        message = cleaned_data.get("message")
        last_name = cleaned_data.get("last_name")
        message_split = re.findall(r'\w+', message)
        if not (5 <= len(message_split) <= 100):
            errors.append("Message should contain between 5 and 100 words!")
        if message.find("http://") != -1 or message.find("https://") != -1:
            errors.append("Message should not contain any links!")
        if message_split[-1] != last_name:
            errors.append("Message should contain your signature at the end!")

        if not errors:
            raise forms.ValidationError(' '.join(errors))

        message.replace("\n", " ")
        message.replace("\r", " ")
        cleaned_message = re.sub(r" {2,}", ' ', message)
        data_to_save['Message'] = cleaned_message

        timestamp = int(time.time())
        current_dir = os.path.dirname(__file__)
        messages_dir = os.path.join(current_dir, '../messages')
        with open(f"{messages_dir}/message_{timestamp}.json", "w+") as file:
            json.dump(data_to_save, file)


class SigninForm(AuthenticationForm):
    stay_signed_in = forms.BooleanField(required=False, initial=False, label="Keep me signed in for a day", widget=forms.CheckboxInput)


class SignupForm(UserCreationForm):

    class Meta:
        model = ProfileModel
        fields = ("username", "email", "first_name", "last_name", "dateOfBirth", "password1", "password2", "country", "city", "addressLineOne", "addressLineTwo", "phoneNumber")
        widgets = {
            "country": CountryChoiceWidget,
            "city": CityChoiceWidget,
            "dateOfBirth": DatePickerInput
        }
        labels = {
            "addressLineOne": "Address first line",
            "addressLineTwo": "Address second line",
            "dateOfBirth": "Date of birth",
            "phoneNumber": "Phone number (with country code)"
        }
        validators = {
            "username": [username],
            "first_name": [starts_with_capital_letter, letters_and_spaces],
            "last_name": [starts_with_capital_letter, letters_and_spaces]
        }


class ProfileChangeForm(UserChangeForm):

    class Meta:
        model = ProfileModel
        fields = ("username", "email")


class ChangePasswordForm(PasswordChangeForm):
    pass


class FilterProductsForm(forms.Form):
    name = forms.CharField(max_length=100, label="Name", required=False)
    categories = CategoryChoiceField(
        queryset=CategoryModel.objects.all().order_by("name"), required=False, empty_label="None")


class ProductAddEditForm(forms.ModelForm):
    unit = forms.CharField(required=True, label="Unit",
                           help_text="Unit should be of format \"Number UnitShortName\". Example: 25 kg.")
    description = forms.CharField(
        required=True, max_length=100, label="Description", widget=forms.Textarea())
    details = ProseEditorFormField(required=False)

    class Meta:
        model = ProductModel
        fields = ['name', 'unit', 'description', 'details', 'categories']
        widgets = {
            "categories": CategoryMultipleChoiceWidget
        }
        validators = {
            'name': [starts_with_capital_letter],
            'unit': [unit_string],
        }
