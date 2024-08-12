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
            grade = request.POST.get('grade') 

            if password == confirmPassword:
                if CustomUser.objects.filter(email=email).exists():
                    messages.info(request, 'Email already existed', extra_tags='emailExist')
                    return redirect('/auth/?form=signup')
                elif CustomUser.objects.filter(username=username).exists():
                    messages.info(request, 'Username already existed', extra_tags='usernameExist')
                    return redirect('/auth/?form=signup')
                else:
                    user = CustomUser.objects.create_user(username=username, email=email, password=password)
                    user.date_of_birth = date(year, month, day)
                    user.role = role
                    user.grade = grade
                    user.grade = grade
                    user.save()

                    user = authenticate(request, email=email, password=password)   
            
                    login(request, user)
                    return redirect('home')
            else:
                messages.info(request, 'Passwords do not match', extra_tags='repass')
                return redirect('/auth/?form=signup')

        elif form_type == 'login':
            email = request.POST.get('email')  
            password = request.POST.get('login-password')

            try:
                user = CustomUser.objects.get(email=email)
            except:
                request.session['email'] = email
                return redirect('/auth/?form=login')

            user = authenticate(request, email=email, password=password)

            if user is not None:
                login(request, user)
                return redirect('home')
            else:
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
    return redirect('login')
