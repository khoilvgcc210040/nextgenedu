from datetime import date
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from home.models import CustomUser, Subjects

import requests

API_KEY = 'sk_test_mtmVaiRS1emm8JXHxpEV3dpwFNied9aO3Yv5l4AFs2'
CLERK_API_URL = 'https://api.clerk.dev/v1/'

def verify_clerk_token(token):
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    response = requests.post(f'{CLERK_API_URL}/verify', json={'token': token}, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def clerk_login(request):
    if request.method == 'POST':
        token = request.POST.get('clerk_token')
        clerk_user = verify_clerk_token(token)
        
        if clerk_user:
            user, created = CustomUser.objects.get_or_create(
                username=clerk_user['username'],
                email=clerk_user['email'],
                defaults={'date_of_birth': clerk_user.get('date_of_birth')}
            )
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Error')
            return redirect('authPage')
    return redirect('authPage')

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
