from django import forms
from .models import User, Role

class AddUserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["full_name", "email", "password", "role"]

class EditUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["full_name", "email", "role", "is_active"]
