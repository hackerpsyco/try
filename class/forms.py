from django import forms
from django.contrib.auth.hashers import make_password
from .models import User, Role, School, ClassSection,FacilitatorSchool

# ---------------- Add User Form ----------------
class AddUserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["full_name", "email", "password", "role"]
        widgets = {
            "full_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Full Name"
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "Email Address"
            }),
            "role": forms.Select(attrs={"class": "form-control"}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.password = make_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


# ---------------- Edit User Form ----------------
class EditUserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=False)

    class Meta:
        model = User
        fields = ["full_name", "email", "password", "role", "is_active"]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "role": forms.Select(attrs={"class": "form-control"}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            user.password = make_password(password)
        if commit:
            user.save()
        return user


# ---------------- Add School Form ----------------
class AddSchoolForm(forms.ModelForm):
    class Meta:
        model = School
        fields = ["name", "udise", "block", "district", "status", "profile_image"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "udise": forms.TextInput(attrs={"class": "form-control"}),
            "block": forms.TextInput(attrs={"class": "form-control"}),
            "district": forms.TextInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-control"}),
        }


# ---------------- Edit School Form ----------------
class EditSchoolForm(forms.ModelForm):
    class Meta:
        model = School
        fields = [
            "name", "udise", "block", "district", "status",
            "enrolled_students", "avg_attendance_pct", "validation_score",
            "profile_image"
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, (forms.TextInput, forms.NumberInput, forms.EmailInput)):
                field.widget.attrs["placeholder"] = field.label


# ---------------- Class Section Form ----------------
class ClassSectionForm(forms.ModelForm):
    class Meta:
        model = ClassSection
        fields = ["class_level", "section"]
        widgets = {
            "class_level": forms.Select(attrs={"class": "form-control"}),
            "section": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "A, B, C (optional)",
            }),
        }

    def clean_section(self):
        section = self.cleaned_data.get("section")
        if section:
            return section.strip().upper()
        return section

class AssignFacilitatorForm(forms.ModelForm):

    class Meta:
        model = FacilitatorSchool
        fields = ["facilitator", "school", "is_primary", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Only facilitators (role_id = 2)
        self.fields["facilitator"].queryset = User.objects.filter(role_id=2)

        # Optional UI improvements
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                "class": "form-control"
            })
