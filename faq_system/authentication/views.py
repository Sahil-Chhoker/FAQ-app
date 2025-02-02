import re
from typing import List

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods


class LoginView(View):
    """
    Handles user authentication and login functionality.
    Supports remember me option and next page redirection.
    """

    template_name = "authentication/login.html"

    @method_decorator(csrf_protect)
    def get(self, request):
        """Return login page or redirect if already authenticated."""
        if request.user.is_authenticated:
            return redirect("/")
        return render(request, self.template_name)

    @method_decorator(csrf_protect)
    def post(self, request):
        """Process login form submission with validation."""
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        remember_me = request.POST.get("remember_me") == "on"

        if not email or not password:
            messages.error(request, "Please fill in all fields.")
            return redirect("login")

        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Please enter a valid email address.")
            return redirect("login")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "Invalid email or password.")
            return redirect("login")

        user = authenticate(request, username=user.username, password=password)
        if user is None:
            messages.error(request, "Invalid email or password.")
            return redirect("login")

        if not user.is_active:
            messages.error(request, "This account has been deactivated.")
            return redirect("login")

        login(request, user)

        if not remember_me:
            request.session.set_expiry(0)

        next_page = request.GET.get("next")
        if next_page and next_page.startswith("/"):
            return redirect(next_page)

        return redirect("/")


class SignupView(View):
    """
    Handles new user registration with comprehensive validation.
    Validates username, email, and password requirements.
    """

    template_name = "authentication/signup.html"

    @method_decorator(csrf_protect)
    def get(self, request):
        """Return signup page or redirect if already authenticated."""
        if request.user.is_authenticated:
            return redirect("/")
        return render(request, self.template_name)

    @method_decorator(csrf_protect)
    def post(self, request):
        """Process signup form submission with validation."""
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip().lower()
        password1 = request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")

        errors = self.validate_signup(username, email, password1, password2)
        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect("signup")

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username, email=email, password=password1
                )
                login(request, user)
                messages.success(
                    request,
                    f"Welcome {username}! Your account has been created successfully.",
                )
                return redirect("/")
        except Exception:
            messages.error(request, "An error occurred during signup.")
            return redirect("signup")

    def validate_signup(
        self, username: str, email: str, password1: str, password2: str
    ) -> List[str]:
        """
        Validates signup data with comprehensive checks.

        Args:
            username: Must be 3+ chars, alphanumeric with underscore
            email: Must be valid and unique
            password1: Must be 8+ chars with upper, lower, and number
            password2: Must match password1

        Returns:
            List of validation error messages, empty if valid
        """
        errors = []

        # Username validation
        if not username:
            errors.append("Username is required.")
        elif len(username) < 3:
            errors.append("Username must be at least 3 characters long.")
        elif not re.match(r"^[a-zA-Z0-9_]+$", username):
            errors.append(
                "Username can only contain letters, numbers, and underscores."
            )
        elif User.objects.filter(username=username).exists():
            errors.append("This username is already taken.")

        # Email validation
        if not email:
            errors.append("Email is required.")
        else:
            try:
                validate_email(email)
                if User.objects.filter(email=email).exists():
                    errors.append("This email is already registered.")
            except ValidationError:
                errors.append("Please enter a valid email address.")

        # Password validation
        if not password1:
            errors.append("Password is required.")
        elif len(password1) < 8:
            errors.append("Password must be at least 8 characters long.")
        elif not re.search(r"[A-Z]", password1):
            errors.append("Password must contain at least one uppercase letter.")
        elif not re.search(r"[a-z]", password1):
            errors.append("Password must contain at least one lowercase letter.")
        elif not re.search(r"\d", password1):
            errors.append("Password must contain at least one number.")
        elif password1 != password2:
            errors.append("Passwords do not match.")

        return errors


@login_required
def profile_view(request):
    """Display user profile page for authenticated users."""
    return render(request, "authentication/profile.html")


@login_required
def logout_view(request):
    """Handle user logout and redirect to login page."""
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect("login")


@login_required
@csrf_protect
@require_http_methods(["GET", "POST"])
def delete_account(request):
    """
    Handle account deletion with password confirmation.
    Deletes user account after verifying password.
    """
    if request.method == "POST":
        password = request.POST.get("password", "")
        user = request.user

        if user.check_password(password):
            try:
                with transaction.atomic():
                    user.delete()
                    logout(request)
                    messages.success(
                        request, "Your account has been permanently deleted."
                    )
                    return redirect("/")
            except Exception:
                messages.error(
                    request, "An error occurred while deleting your account."
                )
        else:
            messages.error(request, "Invalid password.")

    return render(request, "authentication/delete_account.html")
