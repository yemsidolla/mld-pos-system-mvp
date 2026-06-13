from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from core.capabilities import CAPABILITY_GROUPS

from .models import Role, StaffProfile

User = get_user_model()


def assignable_role_choices(for_owner):
    """Role choices for the user forms. Managers may only assign built-in,
    non-Owner roles; Owners may assign any role (incl. custom ones)."""
    roles = Role.objects.all()
    if not for_owner:
        roles = roles.filter(is_builtin=True).exclude(slug="OWNER")
    return [(r.slug, r.name) for r in roles]


class RoleForm(forms.Form):
    """Create or rename a custom role and choose its capabilities."""

    name = forms.CharField(max_length=80)
    capabilities = forms.MultipleChoiceField(
        choices=[(key, label) for _group, items in CAPABILITY_GROUPS for key, label in items],
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, instance=None, **kwargs):
        self.instance = instance
        super().__init__(*args, **kwargs)
        if instance is not None and not self.is_bound:
            self.fields["name"].initial = instance.name
            self.fields["capabilities"].initial = list(instance.capabilities or [])

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if not name:
            raise forms.ValidationError("Role name is required.")
        clash = Role.objects.filter(name__iexact=name)
        if self.instance is not None:
            clash = clash.exclude(pk=self.instance.pk)
        if clash.exists():
            raise forms.ValidationError("A role with this name already exists.")
        return name


class StaffUserCreateForm(forms.Form):
    username = forms.CharField(max_length=150)
    first_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)
    role = forms.ChoiceField(choices=[])
    password = forms.CharField(widget=forms.PasswordInput, min_length=8)

    def __init__(self, *args, allowed_roles=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["role"].choices = allowed_roles if allowed_roles is not None else assignable_role_choices(True)

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
    role = forms.ChoiceField(choices=[])
    is_active = forms.BooleanField(required=False)
    new_password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        help_text="Leave blank to keep the current password.",
    )

    def __init__(self, *args, allowed_roles=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["role"].choices = allowed_roles if allowed_roles is not None else assignable_role_choices(True)

    def clean_new_password(self):
        password = self.cleaned_data.get("new_password", "")
        if password:
            validate_password(password)
        return password
