from django.core.mail import send_mail
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.views import (LoginView, PasswordResetView,
                                       PasswordChangeView,
                                       PasswordChangeDoneView,
                                       PasswordResetDoneView)

from foodgram.settings import ADMIN_EMAIL

from .forms import CreationForm


class SignUp(CreateView):
    form_class = CreationForm
    success_url = '/auth/login/'
    template_name = 'signup.html'

    def form_valid(self, form):
        email = form.cleaned_data['email']
        self.send_mail_ls(email)
        return super().form_valid(form)

    def send_mail_ls(self, email):
        send_mail(
            'Регистрация',
            'Регистрация прошла успешно!',
            ADMIN_EMAIL,
            [email],
            fail_silently=False
        )


class Login(LoginView):
    template_name = 'login.html'


class PassReset(PasswordResetView):
    success_url = reverse_lazy('pass_reset_done')
    template_name = 'password_reset_form.html'


class PassChange(PasswordChangeView):
    success_url = reverse_lazy('pass_change_done')
    template_name = 'password_change_form.html'


class PassChangeDone(PasswordChangeDoneView):
    template_name = 'password_change_done.html'


class PassResetDone(PasswordResetDoneView):
    template_name = 'password_reset_done.html'
