from django import forms
from .models import User, Role, School


class AddUserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["full_name", "email", "password", "role"]


class EditUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["full_name", "email", "password", "role", "is_active"]


class AddSchoolForm(forms.ModelForm):
    class Meta:
        model = School
        fields = [
            "name",
            "udise",
            "block",
            "district",
            "status",
            "enrolled_students",
            "avg_attendance_pct",
            "validation_score",
            "profile_image",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(
                field.widget,
                (forms.TextInput, forms.NumberInput, forms.EmailInput),
            ):
                field.widget.attrs["placeholder"] = field.label


class EditSchoolForm(forms.ModelForm):
    class Meta:
        model = School
        fields = [
            "name",
            "udise",
            "block",
            "district",
            "status",
            "enrolled_students",
            "avg_attendance_pct",
            "validation_score",
            "profile_image",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(
                field.widget,
                (forms.TextInput, forms.NumberInput, forms.EmailInput),
            ):
                field.widget.attrs["placeholder"] = field.label
