from pathlib import Path

from django import forms

from .models import BatchUploadJob


class BatchUploadForm(forms.Form):
    target = forms.ChoiceField(choices=BatchUploadJob.Target.choices)
    file = forms.FileField()

    def clean_file(self):
        uploaded_file = self.cleaned_data["file"]
        extension = Path(uploaded_file.name).suffix.lower()
        if extension not in {".csv", ".xlsx"}:
            raise forms.ValidationError("Only CSV and XLSX files are supported.")
        return uploaded_file
