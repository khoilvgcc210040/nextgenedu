from datetime import date
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from home.models import CustomUser

def home(request):
    context = {}
    return render(request, 'home.html', context)

def authPage(request):
    if request.method == 'POST':
        form_type = request.POST.get('form', 'signup')

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
                messages.info(request, '❗ This email is already registered. Please use a different email address.', extra_tags='emailExist')
                errors = True

            if CustomUser.objects.filter(username=username).exists():
                messages.info(request, '❗ This username is already taken. Please choose a different username.', extra_tags='usernameExist')
                errors = True

            if password != confirmPassword:
                messages.info(request, '❗ The passwords do not match. Please check and re-enter them.', extra_tags='repass')
                errors = True

            if errors:
                return redirect('/auth/?form=signup')
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

            try:
                user = CustomUser.objects.get(email=email)
            except:
                messages.info(request, 'Email has not already existed', extra_tags='notUser')
                request.session['email'] = email
                return redirect('/auth/?form=login')

            user = authenticate(request, email=email, password=password)

            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.info(request, 'Email has not already existed1', extra_tags='notUser')
                request.session['email'] = email
                return redirect('/auth/?form=login')
    else:
        form_type = request.POST.get('form', 'signup')
        context = {
            'form_type': form_type,
            'email': request.session.get('email', '')
        }
        return render(request, 'auth.html', context)
    
def logoutPage(request):
    logout(request)
    return redirect('home')
