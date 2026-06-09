from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from .models import StaffProfile

User = get_user_model()


class StaffUserCreateForm(forms.Form):
    username = forms.CharField(max_length=150)
    first_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)
    role = forms.ChoiceField(choices=StaffProfile.Role.choices)
    password = forms.CharField(widget=forms.PasswordInput, min_length=8)

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if not username:
            raise forms.ValidationError("Username is required.")
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("A user with this username already exists.")
        return username

    def clean_password(self):
        password = self.cleaned_data["password"]
        validate_password(password)
        return password


class StaffUserEditForm(forms.Form):
    first_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)
    role = forms.ChoiceField(choices=StaffProfile.Role.choices)
    is_active = forms.BooleanField(required=False)
    new_password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        help_text="Leave blank to keep the current password.",
    )

    def clean_new_password(self):
        password = self.cleaned_data.get("new_password", "")
        if password:
            validate_password(password)
        return password
