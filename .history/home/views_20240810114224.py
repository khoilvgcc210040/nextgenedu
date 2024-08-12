from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import 
from django.contrib import messages

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
            day = request.POST.get('day')
            month = request.POST.get('month')
            year = request.POST.get('year')
            role = request.POST.get('role')
            grade = request.POST.get('grade') 

            if CustomUser.objects.filter(email=email).exists():
                messages.info(request, _('Email already existed'), extra_tags='emailExist')
                return redirect('register')
            else:
                request.session['email'] = email
                request.session['password'] = password
                return redirect('register1')

            # Kiểm tra nếu người dùng đã tồn tại
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists.')
                return redirect('/auth/?form=signup')
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists.')
                return redirect('/auth/?form=signup')

            # Tạo người dùng mới
            user = User.objects.create_user(username=username, email=email, password=password)
            user.profile.day_of_birth = day
            user.profile.month_of_birth = month
            user.profile.year_of_birth = year
            user.profile.role = role
            if grade:
                user.profile.grade = grade
            user.save()

            # Tự động đăng nhập sau khi đăng ký thành công
            login(request, user)
            return redirect('home')  # Chuyển hướng đến trang chủ hoặc trang cần thiết

        elif form_type == 'login':
            print("login")
            # Xử lý đăng nhập
            email = request.POST.get('email')  # Use `.get()` to safely access POST data
            password = request.POST.get('confirm-password')  # Use `.get()` to avoid MultiValueDictKeyError

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
