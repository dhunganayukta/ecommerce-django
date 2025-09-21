from email.message import EmailMessage
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.views.generic import View
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings
from .utils import generate_token,TokenGenerator

# -----------------------
# Signup View
# -----------------------
def signup(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        # Check passwords
        if password != confirm_password:
            messages.warning(request, "Passwords do not match.")
            return redirect('/authen/signup/')

        # Check username/email
        if User.objects.filter(username=username).exists():
            messages.info(request, "Username already exists.")
            return redirect('/authen/signup/')
        if User.objects.filter(email=email).exists():
            messages.info(request, "Email already exists.")
            return redirect('/authen/signup/')

        # Create inactive user
        user = User.objects.create_user(username=username, email=email, password=password)
        user.is_active = False
        user.save()

        # Send activation email
        email_subject = "Activate Your Account"
        message = render_to_string('activate.html', {
            'user': user,
            'domain': request.get_host(),
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': generate_token.make_token(user)
        })
        email=EmailMessage(
            email_subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
        )
        email.content_subtype = "html"
        email.send(fail_silently=False)

        messages.success(request, "Account created! Check your email to activate your account.")
        return redirect('/authen/login/')

    return render(request, "signup.html")


# -----------------------
# Activate Account
# -----------------------
class ActivateAccountView(View):
    def get(self, request, *args, **kwargs):
        uidb64 = kwargs.get('uidb64')
        token = kwargs.get('token')

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except Exception:
            user = None

        if user is not None and generate_token.check_token(user, token):
            user.is_active = True
            user.save()
            messages.success(request, "Account activated! You can now login.")
            return redirect('/authen/login/')
        else:
            messages.error(request, "Activation link is invalid!")
            return redirect('/authen/signup/')


# -----------------------
# Login View
# -----------------------
def handlelogin(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect('/')  # Redirect to home
            else:
                messages.warning(request, "Account not activated. Check your email.")
                return redirect('/authen/login/')
        else:
            messages.error(request, "Invalid username or password.")
            return redirect('/authen/login/')

    return render(request, "login.html")


# -----------------------
# Logout View
# -----------------------
def handlelogout(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect('/authen/login/')
