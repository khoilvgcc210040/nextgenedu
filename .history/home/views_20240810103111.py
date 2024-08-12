from django.shortcuts import render

def home(request):
    context = {}
    return render(request, 'home.html', context)

def authPage(request):
    if request.method == 'POST':
        form_type = request.GET.get('form', 'signup')  # Kiểm tra form hiện tại là đăng ký hay đăng nhập

        if form_type == 'signup':
            # Xử lý đăng ký
            email = request.POST['email']
            username = request.POST['username']
            password = request.POST['password']
            day = request.POST['day']
            month = request.POST['month']
            year = request.POST['year']
            role = request.POST['role']
            grade = request.POST.get('grade')  # Có thể không bắt buộc

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
            # Xử lý đăng nhập
            email = request.POST['email']
            password = request.POST['password']
            user = authenticate(request, username=User.objects.get(email=email).username, password=password)

            if user is not None:
                login(request, user)
                return redirect('home')  # Chuyển hướng đến trang chủ hoặc trang cần thiết
            else:
                messages.error(request, 'Invalid login credentials')
                return redirect('/auth/?form=login')

    else:
        form_type = request.GET.get('form', 'signup')
        return render(request, 'auth.html', {'form_type': form_type})
