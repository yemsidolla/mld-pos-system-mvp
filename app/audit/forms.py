from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q

from .models import AuditLog


class AuditLogFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        max_length=120,
        label="Search",
        help_text="Object, ID, module, user, action, or IP.",
    )
    action = forms.ChoiceField(
        required=False,
        choices=[("", "All actions")] + list(AuditLog.Action.choices),
    )
    module = forms.CharField(required=False, max_length=80)
    object_type = forms.ChoiceField(required=False, choices=[("", "All object types")], label="Object Type")
    user = forms.ModelChoiceField(
        required=False,
        queryset=get_user_model().objects.order_by("username"),
        empty_label="All users",
    )
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        object_types = (
            AuditLog.objects.exclude(object_type="")
            .order_by("object_type")
            .values_list("object_type", flat=True)
            .distinct()
        )
        self.fields["object_type"].choices = [("", "All object types")] + [
            (object_type, object_type) for object_type in object_types
        ]

    def filter(self, queryset):
        """Apply the cleaned filters to ``queryset``. Read-only."""
        if not self.is_valid():
            return queryset
        data = self.cleaned_data
        if data.get("q"):
            query = data["q"]
            queryset = queryset.filter(
                Q(action__icontains=query)
                | Q(module__icontains=query)
                | Q(object_type__icontains=query)
                | Q(object_id__icontains=query)
                | Q(object_display__icontains=query)
                | Q(ip_address__icontains=query)
                | Q(user__username__icontains=query)
            )
        if data.get("action"):
            queryset = queryset.filter(action=data["action"])
        if data.get("module"):
            queryset = queryset.filter(module__icontains=data["module"])
        if data.get("object_type"):
            queryset = queryset.filter(object_type=data["object_type"])
        if data.get("user"):
            queryset = queryset.filter(user=data["user"])
        if data.get("date_from"):
            queryset = queryset.filter(created_at__date__gte=data["date_from"])
        if data.get("date_to"):
            queryset = queryset.filter(created_at__date__lte=data["date_to"])
        return queryset
