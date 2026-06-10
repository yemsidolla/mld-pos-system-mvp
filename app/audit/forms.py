from django import forms
from django.contrib.auth import get_user_model

from .models import AuditLog


class AuditLogFilterForm(forms.Form):
    action = forms.ChoiceField(
        required=False,
        choices=[("", "All actions")] + list(AuditLog.Action.choices),
    )
    module = forms.CharField(required=False, max_length=80)
    user = forms.ModelChoiceField(
        required=False,
        queryset=get_user_model().objects.order_by("username"),
        empty_label="All users",
    )
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))

    def filter(self, queryset):
        """Apply the cleaned filters to ``queryset``. Read-only."""
        if not self.is_valid():
            return queryset
        data = self.cleaned_data
        if data.get("action"):
            queryset = queryset.filter(action=data["action"])
        if data.get("module"):
            queryset = queryset.filter(module__icontains=data["module"])
        if data.get("user"):
            queryset = queryset.filter(user=data["user"])
        if data.get("date_from"):
            queryset = queryset.filter(created_at__date__gte=data["date_from"])
        if data.get("date_to"):
            queryset = queryset.filter(created_at__date__lte=data["date_to"])
        return queryset
