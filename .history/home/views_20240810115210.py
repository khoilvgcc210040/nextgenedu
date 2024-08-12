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
            day = request.POST.get('day')
            month = request.POST.get('month')
            year = request.POST.get('year')
            role = request.POST.get('role')
            grade = request.POST.get('grade') 

            if

        elif form_type == 'login':
            email = request.POST.get('email')  # Use `.get()` to safely access POST data
            password = request.POST.get('login-password')  # Use `.get()` to avoid MultiValueDictKeyError

            if not password:
                messages.error(request, 'Password is required.')
                return redirect('/auth/?form=login')

            try:
                user = authenticate(request, username=User.objects.get(email=email).username, password=password)
            except User.DoesNotExist:
                messages.error(request, 'Invalid login credentials')
                return redirect('/auth/?form=login')

            if user is not None:
                login(request, user)
                return redirect('home')  # Chuyển hướng đến trang chủ hoặc trang cần thiết
            else:
                messages.error(request, 'Invalid login credentials')
                return redirect('/auth/?form=login')

    else:
        form_type = request.GET.get('form', 'signup')
        return render(request, 'auth.html', {'form_type': form_type})
    
def logoutPage(request):
    logout(request)
    return redirect('login')
