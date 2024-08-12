from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from home.models import CustomUser, Subjects

from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.forms import SetPasswordForm
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.core.mail import send_mail

def home(request):
    if 'login_email' in request.session:
        del request.session['login_email']
    if 'signup_data' in request.session:
        del request.session['signup_data']
    context = {}
    return render(request, 'home.html', context)

def authPage(request):
    if request.method == 'POST':
        form_type = request.POST.get('form', 'signup')
        signup_error = False
        login_error = False

        if form_type == 'signup':
            email = request.POST.get('email') 
            username = request.POST.get('username')
            password = request.POST.get('password')
            confirmPassword = request.POST.get('confirm-password')
            day = int(request.POST.get('day'))
            month = int(request.POST.get('month'))
            year = int(request.POST.get('year'))
            role = request.POST.get('role')
            grade = request.POST.get('grade') 
            terms = request.POST.get('terms') == 'on'

            errors = False

            if CustomUser.objects.filter(email=email).exists():
                messages.info(request, '❌ This email is already registered. Please use a different email address.', extra_tags='signup')
                errors = True

            if CustomUser.objects.filter(username=username).exists():
                messages.info(request, '❌ This username is already taken. Please choose a different username.', extra_tags='signup')
                errors = True

            if password != confirmPassword:
                messages.info(request, '❌ The passwords do not match. Please check and re-enter them.', extra_tags='signup')
                errors = True

            if errors:
                signup_error = True
                request.session['signup_data'] = {
                    'email': email,
                    'username': username,
                    'day': day,
                    'month': month,
                    'year': year,
                    'role': role,
                    'grade': grade,
                    'terms': terms
                }
                return redirect('/auth/?form=signup&signup_error=True')
            else:
                user = CustomUser.objects.create_user(username=username, email=email, password=password)
                user.date_of_birth = date(year, month, day)
                user.role = role
                user.grade = grade
                user.terms_accepted = terms
                user.save()

                user = authenticate(request, email=email, password=password)   
                login(request, user)
                return redirect('home')

        elif form_type == 'login':
            email = request.POST.get('email')  
            password = request.POST.get('login-password')

            user = authenticate(request, email=email, password=password)

            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.info(request, 'Oops. Something went wrong 😅. Please try again.', extra_tags='login')
                login_error = True
                request.session['login_email'] = email
                return redirect('/auth/?form=login&login_error=True')
    else:
        form_type = request.POST.get('form', 'signup')
        signup_error = request.GET.get('signup_error', 'False') == 'True'
        login_error = request.GET.get('login_error', 'False') == 'True'
        signup_data = request.session.pop('signup_data', {})
        days = list(range(1, 32)) 
        months = {i: month for i, month in enumerate(["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], start=1)}
        years = list(range(1900, 2024 + 1)) 
        context = {
            'form_type': form_type,
            'signup_error': signup_error,
            'login_error': login_error,
            'email': signup_data.get('email', ''),
            'username': signup_data.get('username', ''),
            'day': signup_data.get('day', ''),
            'month': signup_data.get('month', ''),
            'year': signup_data.get('year', ''),
            'role': signup_data.get('role', ''),
            'grade': signup_data.get('grade', ''),
            'terms': signup_data.get('terms', False),
            'days': days,
            'months': months,
            'years': years,
            'login_email': request.session.get('login_email') if request.session.get('login_email') else "",
        }
        return render(request, 'auth.html', context)
    
def logoutPage(request):
    logout(request)
    return redirect('home')

def subjects(request):
    subjects = Subjects.objects.all() 
    context = {
        'subjects' : subjects
    }
    return render(request, 'subjects.html', context)

import logging
logger = logging.getLogger(__name__)

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        associated_users = CustomUser.objects.filter(email=email)
        if associated_users.exists():
            for user in associated_users:
                subject = "Password Reset Requested"
                email_template_name = "password_reset_email.html"
                uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
                logger.debug(f'Generated uidb64: {uidb64}')  # Debug line
                c = {
                    "email": user.email,
                    'domain': 'localhost:8000',  # Your development domain
                    'site_name': 'Website',
                    "uidb64": uidb64,  # Ensure this is 'uidb64'
                    "user": user,
                    'token': default_token_generator.make_token(user),
                    'protocol': 'http',
                }
                email = render_to_string(email_template_name, c)
                send_mail(subject, email, 'NextGenEdu <khoilieuct03@gmail.com>', [user.email], fail_silently=False)
            return render(request, 'check_your_email.html')
        else:
            messages.error(request, 'This email does not exist in our system.')
            return redirect('forgot_password')
    return render(request, 'forgot_password.html')


def reset_password(request, uidb64=None, token=None):
    if uidb64 is not None and token is not None:
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            if request.method == 'POST':
                new_password = request.POST.get('new_password')
                confirm_password = request.POST.get('confirm_password')

                if new_password == confirm_password:
                    user.set_password(new_password)
                    user.save()
                    messages.success(request, 'Your password has been successfully changed.')
                    return redirect('login')
                else:
                    messages.error(request, 'Passwords do not match. Please try again.')
                    return redirect(request.path)
            return render(request, 'reset_password.html')
        else:
            messages.error(request, 'The reset link is invalid or has expired.')
            return redirect('forgot_password')
    else:
        messages.error(request, 'Invalid request.')
        return redirect('forgot_password')
