from .models import User
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django import forms


class SigninForm(UserCreationForm):
    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email', 'address',
            'phone_number'
        ]


class LoginForm(AuthenticationForm):
    pass


class ContactForm(forms.Form):
    content = forms.CharField(
        max_length=255, required=True,
        label=''
    )
    content.widget.attrs.update(
        {'placeholder': 'Enter your address/postcode to order'}
    )
