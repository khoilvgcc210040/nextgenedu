from datetime import date, datetime, timedelta, timezone
import json
import math
from django.conf import settings
from django.db.models import Avg
from urllib.parse import urlencode
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_backends
from django.contrib import messages
from django.urls import reverse
from home.models import AcademicYear, Answer, AnsweredQuestion, BlockedParticipant, ChatMessage, Classroom, Comment, CustomUser, FavoriteClassroom, Participant, Question, QuizResult, Section, StudentFile, Subjects, Submission, SubmissionFile, SubsectionFile

from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.forms import SetPasswordForm
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt

import os
import joblib
from dotenv import load_dotenv
import openai
from openai.error import RateLimitError

load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')


model = joblib.load(os.path.join(settings.BASE_DIR, 'education_classification_model.pkl'))
vectorizer = joblib.load(os.path.join(settings.BASE_DIR, 'vectorizer.pkl'))
label_encoder = joblib.load(os.path.join(settings.BASE_DIR, 'label_encoder.pkl'))
User = get_user_model()

def get_chatgpt_response(question):
    try:
        openai.api_key = os.getenv('OPENAI_API_KEY')
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": question},
            ]
        )
        return response['choices'][0]['message']['content']
    except RateLimitError:
        return "Sorry, we're experiencing high traffic right now. Please try again later."


def classify(request):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        user_message = data.get('message')

        X_new = vectorizer.transform([user_message])

        predicted_label = model.predict(X_new)[0]
        label_text = label_encoder.inverse_transform([predicted_label])[0]

        if label_text == "education":
            response_message = get_chatgpt_response(user_message)
        else:
            response_message = "Sorry, I can only help with educational questions."

        return JsonResponse({'response': response_message})
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)

from django.utils import timezone
from datetime import timedelta
@login_required
def chatbot(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_message = data.get('message')
        reset_days = data.get('reset_days')
        delete_history = data.get('delete_history', False)
        set_reset_days = data.get('set_reset_days', False)

        if delete_history:
            Chatbot.objects.filter(user=request.user).delete()
            return JsonResponse({'response': 'Chat history deleted.'})

        if set_reset_days:
            request.user.reset_days = int(reset_days)
            request.user.save()
            return JsonResponse({'response': 'Reset days set.'})

        if reset_days:
            reset_date = timezone.now() - timedelta(days=int(reset_days))
            Chatbot.objects.filter(user=request.user, timestamp__lt=reset_date).delete()

        X_new = vectorizer.transform([user_message])
        predicted_label = model.predict(X_new)[0]
        label_text = label_encoder.inverse_transform([predicted_label])[0]

        if label_text == "education":
            response_message = get_chatgpt_response(user_message)
        else:
            response_message = "Sorry, I can only help with educational questions."

        chat_message = Chatbot.objects.create(
            user=request.user,
            message=user_message,
            response=response_message
        )

        return JsonResponse({'response': response_message})

    # Xóa các tin nhắn cũ khi người dùng tải trang
    reset_days = request.user.reset_days
    if reset_days:
        reset_date = timezone.now() - timedelta(days=int(reset_days))
        Chatbot.objects.filter(user=request.user, timestamp__lt=reset_date).delete()

    chat_messages = Chatbot.objects.filter(user=request.user).order_by('timestamp')
    return render(request, 'chatbot.html', {'chat_messages': chat_messages, 'reset_days': reset_days})

def home(request):
    if 'login_email' in request.session:
        del request.session['login_email']
    if 'signup_data' in request.session:
        del request.session['signup_data']

    subjects = Subjects.objects.all().order_by('grade')
    grouped_subjects = {}
    for subject in subjects:
        if subject.grade not in grouped_subjects:
            grouped_subjects[subject.grade] = []
        grouped_subjects[subject.grade].append(subject)

    context = {
        'grouped_subjects': grouped_subjects
    }
    return render(request, 'home.html', context)

from django.utils.crypto import get_random_string
def send_otp(email):
    otp = get_random_string(length=6, allowed_chars='0123456789')
    send_mail(
        'Your OTP Code',
        f'Your OTP code is {otp}',
        'your-email@example.com',  # Replace with your email
        [email],
        fail_silently=False,
    )
    return otp

def verify_otp(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        otp = data.get('otp')

        if otp == request.session.get('otp'):
            signup_data = request.session.get('signup_data', {})
            user = CustomUser.objects.create_user(
                username=signup_data['username'],
                email=signup_data['email'],
                password=signup_data['password'],
                date_of_birth=date(
                    int(signup_data['year']),
                    int(signup_data['month']),
                    int(signup_data['day'])
                ),
                role=signup_data['role'],
                grade=signup_data['grade'],
                terms_accepted=signup_data['terms'],
                subject=Subjects.objects.get(id=signup_data['subject']) if signup_data['subject'] else None
            )
                
            del request.session['signup_data']
            del request.session['otp']

            backend = get_backends()[0]
            user.backend = f'{backend.__module__}.{backend.__class__.__name__}'
            login(request, user)
            next_url = request.session.pop('next', None)
            if (next_url):
                return JsonResponse({'success': True, 'redirect_url': reverse(next_url)})
            return JsonResponse({'success': True, 'redirect_url': reverse('home')})
        else:
            return JsonResponse({'success': False})

def resend_otp(request):
    if request.method == 'POST':
        email = request.session.get('signup_data', {}).get('email')
        otp = send_otp(email)
        request.session['otp'] = otp
        return JsonResponse({'success': True})

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
            day = int(request.POST.get('day')) if request.POST.get('day') else None
            month = int(request.POST.get('month')) if request.POST.get('month') else None
            year = int(request.POST.get('year')) if request.POST.get('year') else None
            role = request.POST.get('role')
            terms = request.POST.get('terms') == 'on'
            subject = None
            grade = None

            if role == 'teacher':
                subject_id = request.POST.get('subject')
                if subject_id:
                    subject = Subjects.objects.get(id=subject_id)
                    grade = subject.grade
            elif role == 'student':
                grade = request.POST.get('grade')

            errors = False

            if not email or not username or not password or not confirmPassword or not day or not month or not year:
                messages.info(request, '❌ Please fill in all the information.', extra_tags='signup')
                errors = True

            if not terms:
                messages.info(request, '❌ Please accept the Terms of Service and Privacy Policy.', extra_tags='signup')
                errors = True   

            if CustomUser.objects.filter(email=email).exists():
                messages.info(request, '❌ This email is already registered. Please use a different email address.', extra_tags='signup')
                errors = True

            if CustomUser.objects.filter(username=username).exists():
                messages.info(request, '❌ This username is already taken. Please choose a different username.', extra_tags='signup')
                errors = True

            if len(password) < 8:
                messages.info(request, '❌ Password must be at least 8 characters long.', extra_tags='signup')
                errors = True

            if password != confirmPassword:
                messages.info(request, '❌ The passwords do not match. Please check and re-enter them.', extra_tags='signup')
                errors = True

            if errors:
                signup_error = True
                request.session['signup_data'] = {
                    'email': email,
                    'username': username,
                    'password': password,
                    'confirmPassword': confirmPassword,
                    'day': day,
                    'month': month,
                    'year': year,
                    'role': role,
                    'subject': subject_id if subject else None,
                    'grade': grade,
                    'terms': terms
                }
                return JsonResponse({'success': False, 'redirect_url': '/auth/?form=signup&signup_error=True'})
            
            else:
                request.session['signup_data'] = {
                    'email': email,
                    'username': username,
                    'password': password,
                    'day': day,
                    'month': month,
                    'year': year,
                    'role': role,
                    'subject': subject_id if subject else None,
                    'grade': grade,
                    'terms': terms
                }

                otp = send_otp(email)
                request.session['otp'] = otp
                return JsonResponse({'success': True}) 

        elif form_type == 'login':
            email = request.POST.get('email')
            password = request.POST.get('login-password')

            user = authenticate(request, email=email, password=password)

            if user is not None:
                # Lấy backend đầu tiên từ danh sách các backend
                backend = get_backends()[0]
                user.backend = f'{backend.__module__}.{backend.__class__.__name__}'
                login(request, user)
                next_url = request.session.pop('next', None)
                if (next_url):
                    return redirect(next_url)
                return redirect('home')
            else:
                login_error = True
                messages.info(request, 'Oops. Something went wrong 😅. Please try again.', extra_tags='login')
                request.session['login_email'] = email
                return redirect('/auth/?form=login&login_error=True')
    else:
        login_error = request.GET.get('login_error', 'False') == 'True'
        signup_error = request.GET.get('signup_error', 'False') == 'True'
        open_otp = request.GET.get('open_otp', 'False') == 'True'
        signup_data = request.session.pop('signup_data', {})
        days = list(range(1, 32))
        months = {i: month for i, month in enumerate(["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], start=1)}
        years = list(range(1900, 2024 + 1))
        subjects = Subjects.objects.all()

        context = {
            'login_error': login_error,
            'signup_error': signup_error,
            'open_otp': open_otp,
            'email': signup_data.get('email', ''),
            'username': signup_data.get('username', ''),
            'password': signup_data.get('password', ''),
            'confirmPassword': signup_data.get('confirmPassword', ''),
            'day': signup_data.get('day', ''),
            'month': signup_data.get('month', ''),
            'year': signup_data.get('year', ''),
            'role': signup_data.get('role', ''),
            'grade': signup_data.get('grade', ''),
            'selected_subject_id': signup_data.get('subject', None),
            'terms': signup_data.get('terms', False),
            'subjects': subjects,
            'days': days,
            'months': months,
            'years': years,
            'login_email': request.session.get('login_email') if request.session.get('login_email') else "",
        }
        return render(request, 'auth.html', context)

from google.oauth2 import id_token
from google.auth.transport import requests
import os

def generate_unique_username(base_username):
    username = base_username
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1
    return username

@csrf_exempt
def auth_receiver(request):
    token = request.POST['credential']

    print(token)

    try:
        user_data = id_token.verify_oauth2_token(
            token, requests.Request(), os.environ['GOOGLE_OAUTH_CLIENT_ID']
        )
    except ValueError:
        return HttpResponse(status=403)

    email = user_data.get('email')
    base_username = user_data.get('name')

    # Kiểm tra xem người dùng đã tồn tại trong database chưa
    try:
        user = CustomUser.objects.get(email=email)
        # Nếu người dùng đã tồn tại, đăng nhập ngay lập tức
        login(request, user, backend='home.backends.EmailBackend')
        next_url = request.session.pop('next', None)
        if next_url:
            return redirect(next_url)
        return redirect('home')
    except CustomUser.DoesNotExist:
        # Nếu người dùng chưa tồn tại, kiểm tra xem username của gg account này có tồn tại trong database hay không
        if User.objects.filter(username=base_username).exists():
            # Nếu có trùng nhau thì mới tạo username duy nhất
            username = generate_unique_username(base_username)
        else:
            # Nếu không thì vẫn lưu username gg account đến session google_user_data
            username = base_username

        password = get_random_string(length=12)
        # Lưu thông tin vào session và chuyển hướng đến trang hoàn thành hồ sơ
        request.session['google_user_data'] = {
            'email': email,
            'username': username,
            'password': password,
        }
        return redirect('complete_profile')
    
def complete_profile(request):
    google_user_data = request.session.get('google_user_data')
    if not google_user_data:
        return redirect('/auth/?form=login') 

    if request.method == 'POST':
        email = google_user_data['email']
        username = google_user_data['username']
        
        role = request.POST.get('role')
        grade = request.POST.get('grade')
        subject_id = request.POST.get('subject')
        password = google_user_data['password']
        day = int(request.POST.get('day'))
        month = int(request.POST.get('month'))
        year = int(request.POST.get('year'))

        # Tạo người dùng mới với thông tin đầy đủ
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            date_of_birth=date(year, month, day),
            terms_accepted=True,
            role=role,
            grade=grade if role == 'student' else None,
            subject=Subjects.objects.get(id=subject_id) if role == 'teacher' else None
        )
        user.save()

        # Gửi email chứa thông tin người dùng và mật khẩu ngẫu nhiên
        subject = "Complete Your Profile - NextGenEdu"
        message = f"""
Hi {username},

Welcome to NextGenEdu! Here are your account details:

Username: {username}
Email: {email}
Password: {password}

Please log in and change your password as soon as possible for security reasons.

Best regards,
NextGenEdu Team
"""
        email = EmailMessage(subject, message, to=[email])
        email.send()



        # Đăng nhập người dùng sau khi hoàn tất hồ sơ
        login(request, user, backend='home.backends.EmailBackend')
        next_url = request.session.pop('next', None)
        if next_url:
            return redirect(next_url)
        return redirect('home')
    else:
        subjects = Subjects.objects.all()
        context = {'subjects': subjects}
        return render(request, 'complete_profile.html', context)

    
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
from django.core.mail import EmailMessage

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        associated_users = CustomUser.objects.filter(email=email)
        if associated_users.exists():
            for user in associated_users:
                subject = "Password Reset Requested"
                email_template_name = "password_reset_email.html"
                uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
                c = {
                    "email": user.email,
                    'domain': 'localhost:8000',
                    'site_name': 'NextGenEdu',
                    "uidb64": uidb64,
                    "user": user,
                    'token': default_token_generator.make_token(user),
                    'protocol': 'http',
                }
                email_body = render_to_string(email_template_name, c)
                email = EmailMessage(
                    subject,
                    email_body,
                    'NextGenEdu <nextgenedu03.info@gmail.com>',
                    [user.email],
                )
                email.content_subtype = "html"  # This is the key line that allows HTML rendering
                email.send()
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
                    return redirect('/auth/?form=login')
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

from django.core.exceptions import ValidationError

def create_classroom(request):
    if request.method == "POST":
        errors = []

        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        school = request.POST.get('school', '').strip()
        academic_year_id = request.POST.get('academic_year')
        status = request.POST.get('status', 'public')
        password = request.POST.get('classroom_password', '').strip()

        if not name:
            errors.append('Classroom name is required.')
        if not school:
            errors.append('School name is required.')
        if not description:
            errors.append('Description is required.')
        if status == 'private' and len(password) < 6:
            errors.append('Password must be at least 6 characters long if the classroom is private.')

        if errors:
            return JsonResponse({'status': 'error', 'errors': errors})

        try:
            academic_year = AcademicYear.objects.get(id=academic_year_id)
        except AcademicYear.DoesNotExist:
            return JsonResponse({'status': 'error', 'errors': ['Invalid academic year.']})

        teacher = request.user
        grade = teacher.grade
        subject = teacher.subject

        try:
            classroom = Classroom(
                name=name,
                description=description,
                school=school,
                academic_year=academic_year,
                subject=subject,
                grade=grade,
                status=status == 'private',
                password=password if status == 'private' else '',
                teacher=teacher,
            )
            classroom.full_clean()
            classroom.save()

            Section.objects.create(classroom=classroom, title="Welcome")
            Participant.objects.create(user=request.user, classroom=classroom, role='teacher')

            return JsonResponse({'status': 'success', 'redirect_url': reverse('manage_classroom_detail', args=[classroom.id])})

        except ValidationError as e:
            return JsonResponse({'status': 'error', 'errors': e.messages})

        except IntegrityError:
            return JsonResponse({'status': 'error', 'errors': ['Classroom with this name already exists for this teacher.']})

    return JsonResponse({'status': 'error', 'errors': ['Invalid request method.']})

def access_join_classroom(request, link):
    classroom = get_object_or_404(Classroom, link=link)
    user = request.user

    # Kiểm tra nếu người dùng đã tham gia classroom
    if user.is_authenticated and Participant.objects.filter(user=user, classroom=classroom).exists():
        return redirect('classroom_detail', id=classroom.id)

    # Nếu classroom là private, yêu cầu password
    if classroom.status:  # status == True tức là private
        if not user.is_authenticated:
            # Người dùng chưa đăng nhập
            request.session['next'] = request.get_full_path()
            return redirect('/auth/?form=login')  # Điều hướng đến trang đăng nhập
        
        if user.role == 'teacher' and user.id != classroom.teacher.id:
            # Chuyển hướng giáo viên đến trang classrooms và hiển thị modal request
            return redirect(f"{reverse('classrooms', args=[classroom.subject.id, classroom.grade])}?show_request_modal=True&classroom_id={classroom.id}")
        
        if request.method == 'POST':
            password = request.POST.get('password')

            if password != '':
                if password == classroom.password:
                    Participant.objects.create(user=user, classroom=classroom, role='student')
                    return redirect('classroom_detail', id=classroom.id)
                else:
                    messages.error(request, 'Incorrect password. Please try again.')
            else:
                messages.error(request, 'Please enter the password.')
    
        return render(request, 'access_join_classroom.html', {
            'classroom': classroom,
            'requires_password': True
        })

    # Nếu classroom là public
    if not user.is_authenticated:
        request.session['next'] = request.get_full_path()
        return redirect('/auth/?form=login')  # Điều hướng đến trang đăng nhập
    
    if user.role == 'teacher' and user.id != classroom.teacher.id:
        return redirect(f"{reverse('classrooms', args=[classroom.subject.id, classroom.grade])}?show_request_modal=True&classroom_id={classroom.id}")

    if request.method == 'POST' and user.is_authenticated:
        Participant.objects.create(user=user, classroom=classroom, role='student')
        return redirect('classroom_detail', id=classroom.id)

    return render(request, 'access_join_classroom.html', {
        'classroom': classroom,
        'requires_password': False
    })


def upload_subsection_file(request, subsection_id):
    subsection = get_object_or_404(Section, id=subsection_id)

    if request.method == 'POST':
        if 'file' in request.FILES:
            file = request.FILES['file']
            subsection_file = SubsectionFile(subsection=subsection, file=file)
            
            try:
                subsection_file.full_clean()
                subsection_file.save()
                return redirect('classroom_detail', subsection.classroom.id)  # Chuyển hướng sau khi upload thành công
            except ValidationError as e:
                return render(request, 'upload_template.html', {'errors': e.messages})

        else:
            return render(request, 'upload_template.html', {'errors': ['No file uploaded']})

    return render(request, 'classroom_detail.html')

@csrf_exempt
def leave_classroom(request, classroom_id):
    user = request.user
    try:
        participant = Participant.objects.get(user=user, classroom_id=classroom_id)
        participant.delete()
        return redirect('classrooms', participant.classroom.subject.id, participant.classroom.grade)
    except Participant.DoesNotExist:
        return redirect('classroom_detail', id=classroom_id)


def classrooms(request, subject_id, grade):
    subject = get_object_or_404(Subjects, id=subject_id, grade=grade)
    status = request.GET.get('status', None)
    user = request.user

    if status is not None:
        classrooms = Classroom.objects.filter(subject=subject, grade=grade, status=status)
    else:
        classrooms = Classroom.objects.filter(subject=subject, grade=grade)
    
    if user.is_authenticated:
        blocked_classrooms = BlockedParticipant.objects.filter(user=user).values_list('classroom_id', flat=True)
        classrooms = classrooms.exclude(id__in=blocked_classrooms)
        participant_classrooms = Participant.objects.filter(user=user, classroom__in=classrooms).values_list('classroom_id', flat=True)
        co_teacher_requests = CoTeacherRequest.objects.filter(requester=user).values_list('classroom_id', flat=True)
    else:
        participant_classrooms = []
        co_teacher_requests = []

    context = {
        'subject': subject,
        'grade': grade,
        'classrooms': classrooms,
        'status': status,
        'participant_classrooms': participant_classrooms,
        'co_teacher_requests': co_teacher_requests,
    }
    return render(request, 'classrooms.html', context)

@login_required
def request_co_teacher(request, classroom_id):
    if request.method == 'POST':
        classroom = get_object_or_404(Classroom, id=classroom_id)
        message = request.POST.get('request_message')
        CoTeacherRequest.objects.create(requester=request.user, classroom=classroom, message=message)
        return JsonResponse({'status': 'success', 'message': 'Request sent successfully!'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)

@login_required
def join_classroom(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id)
    user = request.user

    # Check if the user is already a participant
    if Participant.objects.filter(user=user, classroom=classroom).exists():
        return redirect('classroom_detail', id=classroom_id)

    if request.method == 'POST':
        Participant.objects.create(user=user, classroom=classroom, role='student')
        return redirect('classroom_detail', id=classroom_id)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

import bleach

def enter_password(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id)
    
    if request.method == 'POST':
        entered_password = request.POST.get('password')
        
        # Kiểm tra input rỗng
        if not entered_password:
            return JsonResponse({'status': 'error', 'message': '❌ Password cannot be empty'})
        
        # Làm sạch dữ liệu đầu vào để ngăn chặn XSS
        entered_password = bleach.clean(entered_password)
        
        if entered_password == classroom.password:
            participant_exists = Participant.objects.filter(user=request.user, classroom=classroom).exists()
            
            if not participant_exists:
                Participant.objects.create(user=request.user, classroom=classroom, role='student')
                
            return JsonResponse({'status': 'success', 'redirect_url': reverse('classroom_detail', args=[classroom.id])})
        else:
            return JsonResponse({'status': 'error', 'message': '❌ Incorrect password'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)


@csrf_exempt
def update_classroom(request, classroom_id):
    if request.method == 'POST':
        try:
            classroom = get_object_or_404(Classroom, id=classroom_id)
            name = request.POST.get('name')
            status = request.POST.get('status')
            password = request.POST.get('password')
            if name:
                classroom.name = name
            if status:
                classroom.status = True if status == 'Private' else False
                if classroom.status:
                    classroom.password = password
                else:
                    classroom.password = ''

            classroom.save()
            return JsonResponse({'status': 'success', 'message': 'Classroom updated successfully.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)

@csrf_exempt
def update_allow_chat(request, classroom_id):
    if request.method == 'POST':
        classroom = get_object_or_404(Classroom, id=classroom_id)
        try:
            data = json.loads(request.body)
            allow_chat = data.get('allow_chat')
            classroom.allow_chat = allow_chat
            classroom.save()

            if allow_chat:
                return JsonResponse({'status': 'success', 'message': 'Allow chat enabled!'})
            else:
                return JsonResponse({'status': 'success', 'message': 'Allow chat disabled!'})
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'failed', 'message': 'Invalid JSON'}, status=400)
    return JsonResponse({'status': 'failed', 'message': 'Invalid request method'}, status=400)

@csrf_exempt
def delete_classroom(request, classroom_id):
    if request.method == 'POST':
        try:
            classroom = get_object_or_404(Classroom, id=classroom_id)
            classroom.delete()
            return redirect('classrooms', classroom.subject.id, classroom.grade)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)

@login_required
def classroom_detail(request, id):
    classroom = get_object_or_404(Classroom, id=id)
    sections = Section.objects.filter(classroom=classroom)
    messages = ChatMessage.objects.filter(classroom=classroom).order_by('timestamp')
    is_favorite = FavoriteClassroom.objects.filter(user=request.user, classroom=classroom).exists()
    participants = classroom.participants.all()

    scores_data = []
    for participant in participants:
        if participant.user.role == 'student': 
            quiz_results = QuizResult.objects.filter(
                submission__section__classroom=classroom,
                student=participant.user,
                submission__submission_type='question_test'
            )

            total_score = sum(result.score for result in quiz_results)
            num_tests = quiz_results.count()
            total_time = sum((result.time_taken for result in quiz_results if result.time_taken), timedelta())
            
            # Chuyển đổi total_time thành dạng h:m:s
            total_time_hms = str(total_time)

            scores_data.append({
                'user': participant.user,
                'total_score': total_score,
                'num_tests': num_tests,
                'total_time': total_time_hms,  # Convert to minutes
                'total_time_seconds': total_time.total_seconds()  # Thêm thời gian dưới dạng giây để so sánh
            })

    # Sort by total_score and total_time_seconds for ranking purposes
    scores_data.sort(key=lambda x: (-x['total_score'], -x['total_time_seconds']))

    # Lấy tất cả các submissions trong lớp học
    submissions = Submission.objects.filter(section__classroom=classroom)

    # Lấy kết quả bài kiểm tra của học sinh hiện tại (cho `question_test`)
    quiz_results = {
        quiz_result.submission.id: quiz_result
        for quiz_result in QuizResult.objects.filter(submission__in=submissions.filter(submission_type='question_test'), student=request.user)
    }

    # Lấy StudentFile cho submission loại `assignment` nếu có
    student_files = StudentFile.objects.filter(student=request.user, submission__in=submissions.filter(submission_type='assignment'))

    existing_comment = Comment.objects.filter(user=request.user, classroom=classroom).exists()

    if request.method == 'POST' and not existing_comment:
        comment_text = request.POST.get('comment')
        rating = request.POST.get('rating')

        Comment.objects.create(user=request.user, classroom=classroom, text=comment_text, rating=rating)

        average_rating = Comment.objects.filter(classroom=classroom).aggregate(Avg('rating'))['rating__avg'] or 0.00
        classroom.average_rating = round(average_rating, 2)
        classroom.save()

        return redirect('classroom_detail', id=classroom.id)


    comments = Comment.objects.filter(classroom=classroom).order_by('-created_at')

    range_list = range(1, 6)

    context = {
        'classroom': classroom,
        'sections': sections,
        'participants': participants,
        'scores_data': scores_data,  # Dữ liệu xếp hạng mới
        'submissions': submissions,  # Tất cả submissions
        'quiz_results': quiz_results,  # Kết quả của tất cả các bài kiểm tra của học sinh
        'student_files': student_files,  # Danh sách các StudentFile cho các bài assignment
        'comments': comments,
        'existing_comment': existing_comment,
        'range': range_list, 
        'messages': messages, 
        'is_favorite': is_favorite,
    }
    return render(request, 'classroom_detail.html', context)

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
@login_required
@csrf_exempt
def save_message(request):
    if request.method == 'POST':
        classroom_id = request.POST.get('classroom_id')
        message = request.POST.get('message')
        image = request.FILES.get('image') 
        file = request.FILES.get('file')  # Lấy file đính kèm (Word, PDF)
        classroom = Classroom.objects.get(id=classroom_id)

        chat_message = ChatMessage.objects.create(
            user=request.user,
            classroom=classroom,
            message=message,
            image=image,
            file=file,
            file_size=(math.ceil(file.size / 1024)) if file else 0
        )


        return JsonResponse({
            'status': 'success',
            'username': request.user.username,
            'message': chat_message.message,
            'image_url': chat_message.image.url if chat_message.image else None,
            'file_url': chat_message.file.url if chat_message.file else None, 
            'file_size': chat_message.file_size if chat_message.file else 0
        })

    return JsonResponse({'status': 'error'}, status=400)



def update_section(request, classroom_id, section_id):
    section = get_object_or_404(Section, id=section_id, classroom_id=classroom_id)

    if request.method == 'POST':
        if 'description' in request.POST:
            section.description = request.POST['description']
            section.save()

        # Xử lý upload file
        if 'uploadFile' in request.FILES:
            file = request.FILES['uploadFile']
            SubsectionFile.objects.create(subsection=section, file=file)

        # Xử lý xóa file
        if 'deleteFile' in request.POST and request.POST['deleteFile']:
            file_to_delete = request.POST['deleteFile'].strip()
            subsection_file = SubsectionFile.objects.filter(subsection=section)
            
            # Tìm file cần xóa
            for file in subsection_file:
                if file.file.name.endswith(file_to_delete):
                    file.delete()

        return redirect('classroom_detail', id=classroom_id)


    
def update_submission(request, classroom_id, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)

    if request.method == 'POST':
        # Update description
        if 'description' in request.POST:
            submission.description = request.POST['description']
            submission.save()

        # Handle file upload
        if 'uploadFile' in request.FILES:
            file = request.FILES['uploadFile']
            SubmissionFile.objects.create(submission=submission, file=file)

        # Handle file deletion
        if 'deleteFileSubmission' in request.POST and request.POST['deleteFileSubmission']:
            file_id = request.POST['deleteFileSubmission']
            SubmissionFile.objects.filter(id=file_id).delete()

        return redirect('classroom_detail', id=classroom_id)
    
def update_classroom_description(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id)
    if request.method == 'POST':
        description = request.POST.get('description')
        classroom.description = description
        classroom.save()
        return redirect('classroom_detail', id=classroom.id)
    return HttpResponse("Invalid request", status=400)

@login_required
def submit_assignment(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)
    classroom = submission.section.classroom  # Truy xuất lớp học từ bài nộp
    
    if not submission.is_open():
        return redirect('classroom_detail', id=classroom.id)

    if request.method == 'POST':
        uploaded_file = request.FILES['file']
        StudentFile.objects.create(submission=submission, student=request.user, file=uploaded_file)
        return redirect('classroom_detail', id=classroom.id)

    return render(request, 'submit_assignment.html', {'submission': submission})

@csrf_exempt
def save_remaining_time(request):
    if request.method == 'POST':
        submission_id = request.POST.get('submission_id')
        remaining_time = int(request.POST.get('remaining_time', '0'))
        
        try:
            quiz_result = QuizResult.objects.get(submission_id=submission_id, student=request.user)
            quiz_result.time_taken = timedelta(seconds=remaining_time)
            quiz_result.save()
            return JsonResponse({'status': 'success'})
        except QuizResult.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Quiz result not found'}, status=404)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

def take_quiz(request, submission_id, question_id):
    submission = get_object_or_404(Submission, id=submission_id)
    question = get_object_or_404(Question, id=question_id)
    total_questions = submission.questions.count()

    quiz_result, created = QuizResult.objects.get_or_create(
        submission=submission,
        student=request.user,
        defaults={'correct_answers': 0, 'total_questions': total_questions, 'score': 0.0}
    )
    answered_questions = quiz_result.answered_questions

    if created:
        quiz_result.time_taken = submission.duration
        quiz_result.save()

    remaining_time = quiz_result.time_taken.total_seconds()

    previous_question = Question.objects.filter(submission=submission, id__lt=question_id).last()

    if 'previous' in request.GET:
        quiz_result.answered_questions -= 1
        quiz_result.save()

    answered_question = AnsweredQuestion.objects.filter(quiz_result=quiz_result, question=question).first()
    answered = answered_question is not None
    selected_answer = answered_question.selected_answer.id if answered else None

    return render(request, 'take_quiz.html', {
        'submission': submission,
        'current_question': question,  # Đảm bảo current_question luôn được cập nhật đúng
        'total_questions': total_questions,
        'answered_questions': quiz_result.answered_questions,
        'remaining_time': remaining_time,
        'previous_question': previous_question,
        'answered': answered,
        'selected_answer': selected_answer
    })

def submit_answer(request, submission_id, question_id):
    submission = get_object_or_404(Submission, id=submission_id)
    question = get_object_or_404(Question, id=question_id)
    selected_answer_id = request.POST.get('selected_answer')
    selected_answer = get_object_or_404(Answer, id=selected_answer_id)

    correct = selected_answer.is_correct

    quiz_result, created = QuizResult.objects.get_or_create(
        submission=submission,
        student=request.user,
        defaults={'correct_answers': 0, 'total_questions': submission.questions.count(), 'score': 0.0}
    )

    answered_question, created = AnsweredQuestion.objects.get_or_create(
        quiz_result=quiz_result,
        question=question,
        defaults={'selected_answer': selected_answer}
    )

    if Question.objects.filter(submission=submission, id__gt=question_id).exists():
        quiz_result.answered_questions += 1
        quiz_result.save()

    if created:
        if correct:
            quiz_result.correct_answers += 1
    else:
        if answered_question.selected_answer != selected_answer:
            if answered_question.selected_answer.is_correct:
                quiz_result.correct_answers -= 1
            if correct:
                quiz_result.correct_answers += 1
            answered_question.selected_answer = selected_answer
            answered_question.save()

    quiz_result.total_questions = submission.questions.count()
    quiz_result.score = (quiz_result.correct_answers / quiz_result.total_questions) * 10

    remaining_time = int(request.POST.get('elapsed_time', '0'))
    quiz_result.time_taken = timedelta(seconds=remaining_time)
    quiz_result.save()

    next_question = Question.objects.filter(submission=submission, id__gt=question_id).first()
    if next_question:
        return redirect('take_quiz', submission_id=submission.id, question_id=next_question.id)
    else:
        return redirect('quiz_result', submission_id=submission.id)

def quiz_result(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)
    classroom = submission.section.classroom

    # Lấy kết quả bài kiểm tra của học sinh hiện tại
    quiz_result = get_object_or_404(QuizResult, submission=submission, student=request.user)

    # Chuyển hướng về trang classroom_detail và truyền các tham số cần thiết qua URL
    return redirect('classroom_detail', id=classroom.id)

def exit_quiz(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)
    classroom = submission.section.classroom
    quiz_result = QuizResult.objects.filter(submission=submission, student=request.user).first()
    if quiz_result:
        remaining_time = int(request.POST.get('elapsed_time', '0'))
        quiz_result.time_taken = timedelta(seconds=remaining_time)
        quiz_result.save()
    return redirect('classroom_detail', id=classroom.id)


@login_required
def update_file_submission(request, file_id):
    student_file = get_object_or_404(StudentFile, id=file_id, student=request.user)
    submission = student_file.submission
    classroom = submission.section.classroom  # Truy xuất lớp học từ bài nộp

    if not submission.is_open():
        return redirect('classroom_detail', id=classroom.id)

    if request.method == 'POST':
        student_file.file = request.FILES['file']
        student_file.save()
        return redirect('classroom_detail', id=classroom.id)

    return redirect('classroom_detail', id=classroom.id)

@login_required
def delete_file_submission(request, file_id):
    student_file = get_object_or_404(StudentFile, id=file_id, student=request.user)
    submission = student_file.submission
    classroom = submission.section.classroom  # Truy xuất lớp học từ bài nộp
    
    student_file.delete()
    return redirect('classroom_detail', id=classroom.id)


def setting_classroom(request, id):
    classroom = get_object_or_404(Classroom, id=id)
    blocked_participants = BlockedParticipant.objects.filter(classroom=classroom)
    context = {
        'classroom': classroom,
        'blocked_participants': blocked_participants,
    }
    return render(request, 'setting_classroom.html', context)

@login_required
def unblock_participant(request, classroom_id):
    if request.method == 'POST':
        participant_id = request.POST.get('participant_id')
        participant = get_object_or_404(BlockedParticipant, id=participant_id, classroom_id=classroom_id)
        participant.delete()
        return JsonResponse({'status': 'success', 'message': 'Participant unblocked successfully!'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

def manage_classroom_detail(request, id):
    classroom = get_object_or_404(Classroom, id=id)
    sections = classroom.sections.all()
    participants = classroom.participants.all()
    assignments = Submission.objects.filter(section__classroom=classroom, submission_type='assignment').prefetch_related('student_files')
    question_tests = Submission.objects.filter(section__classroom=classroom, submission_type='question_test')
    num_sections = sections.count()
    num_participants = participants.count()
    parent_sections, child_sections = classroom.count_sections()
    co_teacher_requests = CoTeacherRequest.objects.filter(classroom=classroom)

    context = {
        'classroom': classroom,
        'sections': sections,
        'participants': participants,
        'assignments': assignments,
        'question_tests': question_tests,
        'num_sections': num_sections,
        'num_participants': num_participants,
        'parent_sections': parent_sections,
        'child_sections': child_sections,
        'co_teacher_requests': co_teacher_requests,
    }
    return render(request, 'manage_classroom_detail.html', context)

@csrf_exempt
@login_required
def handle_co_teacher_request(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        request_id = data.get('request_id')
        action = data.get('action')

        try:
            co_teacher_request = CoTeacherRequest.objects.get(id=request_id)
            if action == 'accept':
                # Logic để chấp nhận yêu cầu
                Participant.objects.create(user=co_teacher_request.requester, classroom=co_teacher_request.classroom, role='co_teacher')
                co_teacher_request.delete()
                return JsonResponse({'status': 'success', 'message': 'Request accepted successfully!'})
            elif action == 'reject':
                # Logic để từ chối yêu cầu
                co_teacher_request.delete()
                return JsonResponse({'status': 'success', 'message': 'Request rejected successfully!'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid action.'})
        except CoTeacherRequest.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Request not found.'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)

from datetime import timedelta

def create_section_submission(request):
    if request.method == 'POST':
        classroom_id = request.POST.get('classroom_id')
        action_type = request.POST.get('action_type')
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        classroom = get_object_or_404(Classroom, id=classroom_id)

        if action_type == 'section':
            section_type = request.POST.get('section_type')
            parent_section_id = request.POST.get('parent_section')
            parent_section = None

            if section_type == 'sub':
                parent_section = get_object_or_404(Section, id=parent_section_id)

            section = Section.objects.create(
                classroom=classroom,
                title=title,
                description=description,
                parent_section=parent_section
            )
            section.save()
            if classroom.participants.filter(user__notify_sections=True).exists():
                notify_participants(classroom, 'section', title, classroom.participants.filter(user__notify_sections=True))
            return JsonResponse({'status': 'success', 'message': 'Section/Subsection created successfully!'})

        elif action_type == 'submission':
            submission_type = request.POST.get('submission_type')
            open_date = request.POST.get('open_date')
            close_date = request.POST.get('close_date')
            duration_str = request.POST.get('duration')
            parent_section_id = request.POST.get('parent_section')

            try:
                duration_minutes = int(duration_str)
                duration = timedelta(minutes=duration_minutes)
            except (ValueError, TypeError):
                duration = timedelta(0)

            section = get_object_or_404(Section, id=parent_section_id)

            submission = Submission.objects.create(
                section=section,
                title=title,
                submission_type=submission_type,
                description=description,
                open_date=open_date,
                close_date=close_date,
                duration=duration
            )
            submission.save()
            if classroom.participants.filter(user__notify_sections=True).exists():
                notify_participants(classroom, 'submission', title, classroom.participants.filter(user__notify_sections=True))
            return JsonResponse({'status': 'success', 'message': 'Submission created successfully!'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})

def notify_participants(classroom, item_type, item_title, participants):
    subject = f'New {item_type} added to {classroom.name}'
    message = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Notification</title>
    </head>
    <body>
        <p>Dear Member,</p>
        <p>A new {item_type} titled "{item_title}" has been added to the classroom "{classroom.name}".</p>
        <p>Best regards,<br>Classroom Team</p>
    </body>
    </html>
    """
    recipient_list = [participant.user.email for participant in participants]
    send_mail(subject, message, 'NextGenEdu <nextgenedu03.info@gmail.com>', recipient_list, fail_silently=False, html_message=message)

@csrf_exempt
@login_required
def update_notification_preference(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        request.user.notify_sections = data.get('notify_sections', False)
        request.user.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'failed'}, status=400)

def manage_classroom_list(request):
    user = request.user
    status = request.GET.get('status', None)
    classrooms = Classroom.objects.filter(teacher=user)
    context = {
        'classrooms': classrooms,
        'status': status,
    }
    return render(request, 'manage_classroom_list.html', context)

def question_list(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id, submission_type='question_test')
    questions = submission.questions.all()
    quiz_results = submission.quiz_results.all()
    number_of_participants = quiz_results.count()
    total_participants = submission.section.classroom.participants.count()
    context = {
        'submission': submission,
        'questions': questions,
        'number_of_participants': number_of_participants,
        'total_participants': total_participants,
    }
    
    return render(request, 'question_list.html', context)

from django.utils.dateparse import parse_datetime

@csrf_exempt
def edit_submission_time(request):
    if request.method == 'POST':
        submission_id = request.POST.get('submission_id')
        time_type = request.POST.get('time_type')
        new_time = request.POST.get('new_time')
        
        try:
            submission = Submission.objects.get(id=submission_id)
            if time_type == 'open':
                submission.open_date = parse_datetime(new_time)
            elif time_type == 'close':
                submission.close_date = parse_datetime(new_time)
            submission.save()
            return JsonResponse({'success': True})
        except Submission.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Submission not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@csrf_exempt
def edit_submission_duration(request):
    if request.method == 'POST':
        submission_id = request.POST.get('submission_id')
        new_duration = request.POST.get('new_duration')
        
        try:
            submission = Submission.objects.get(id=submission_id)
            submission.duration = timedelta(minutes=int(new_duration))
            submission.save()
            return JsonResponse({'success': True})
        except Submission.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Submission not found'})
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid duration value'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@csrf_exempt
def edit_assignment_time(request):
    if request.method == 'POST':
        assignment_id = request.POST.get('assignment_id')
        time_type = request.POST.get('time_type')
        new_time = request.POST.get('new_time')
        
        try:
            assignment = Submission.objects.get(id=assignment_id)
            if time_type == 'open':
                assignment.open_date = parse_datetime(new_time)
            elif time_type == 'close':
                assignment.close_date = parse_datetime(new_time)
            assignment.save()
            return JsonResponse({'success': True})
        except Submission.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Assignment not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})
    

def create_question(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id, submission_type='question_test')

    if request.method == 'POST':
        question_text = request.POST.get('question_text')
        options = [
            request.POST.get('option1'),
            request.POST.get('option2'),
            request.POST.get('option3'),
            request.POST.get('option4'),
        ]
        correct_option = int(request.POST.get('correct_option'))

        question = Question.objects.create(submission=submission, text=question_text)

        for idx, option_text in enumerate(options, start=1):
            Answer.objects.create(
                question=question,
                text=option_text,
                is_correct=(idx == correct_option)
            )

        return redirect('question_list', submission_id=submission.id)

    context = {
        'submission': submission,
    }

    return render(request, 'create_question.html', context)

def edit_question(request, submission_id, question_id):
    submission = get_object_or_404(Submission, id=submission_id, submission_type='question_test')
    question = get_object_or_404(Question, id=question_id, submission=submission)

    if request.method == 'POST':
        question_text = request.POST.get('question_text')
        options = [
            request.POST.get('option1'),
            request.POST.get('option2'),
            request.POST.get('option3'),
            request.POST.get('option4'),
        ]
        correct_option = int(request.POST.get('correct_option'))

        # Cập nhật câu hỏi
        question.text = question_text
        question.save()

        # Xóa các đáp án cũ và thêm đáp án mới
        question.answers.all().delete()
        for idx, option_text in enumerate(options, start=1):
            Answer.objects.create(
                question=question,
                text=option_text,
                is_correct=(idx == correct_option)
            )

        return redirect('question_list', submission_id=submission.id)

    context = {
        'submission': submission,
        'question': question,
        'answers': question.answers.all(),
    }
    return render(request, 'edit_question.html', context)

def delete_question(request, submission_id, question_id):
    submission = get_object_or_404(Submission, id=submission_id, submission_type='question_test')
    question = get_object_or_404(Question, id=question_id, submission=submission)

    if request.method == 'POST':
        question.delete()
        return redirect('question_list', submission_id=submission.id)

    context = {
        'submission': submission,
        'question': question,
    }
    return render(request, 'question_list.html', context)


from django.http import JsonResponse

import json

def marking(request, assignment_id):
    assignment = get_object_or_404(Submission, id=assignment_id)
    student_files = assignment.student_files.all()

    total_participants = assignment.section.classroom.participants.filter(user__role='student').count()
    submitted_participants = student_files.filter(student__role='student').values('student').distinct().count()

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            student_file_id = data.get('student_file_id')
            score = data.get('score')
            feedback = data.get('feedback')
            if student_file_id and score:
                try:
                    score = float(score)
                    if 0 <= score <= 10:
                        student_file = get_object_or_404(StudentFile, id=student_file_id)
                        student_file.score = score
                        student_file.feedback = feedback
                        student_file.save()
                        return JsonResponse({'status': 'success', 'message': 'Score updated successfully.'})
                    else:
                        return JsonResponse({'status': 'error', 'message': 'Score must be between 0 and 10.'})
                except ValueError:
                    return JsonResponse({'status': 'error', 'message': 'Invalid score. Please enter a number.'})
            else:
                return JsonResponse({'status': 'error', 'message': 'All fields are required.'})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data.'})

    context = {
        'assignment': assignment,
        'student_files': student_files,
        'total_participants': total_participants,
        'submitted_participants': submitted_participants,
    }

    return render(request, 'marking.html', context)

from django.contrib.auth import update_session_auth_hash
import random
@login_required
def setting(request):
    user = request.user

    if request.method == 'POST':
        if 'save_changes' in request.POST:
            new_email = request.POST.get('email')
            new_username = request.POST.get('username')
            from datetime import date

            year = int(request.POST.get('dob-year'))
            month = int(request.POST.get('dob-month'))
            day = int(request.POST.get('dob-day'))
            user.date_of_birth = date(year, month, day)

            if new_email != user.email:
                if CustomUser.objects.filter(email=new_email).exists():
                    return JsonResponse({'status': 'error', 'message': 'This email is already registered. Please use a different email address.'})
                otp = ''.join(random.choices('0123456789', k=6))
                request.session['otp'] = otp
                request.session['new_email'] = new_email
                send_mail(
                    'Your OTP Code',
                    f'Your OTP code is {otp}',
                    'from@example.com',
                    [new_email],
                    fail_silently=False,
                )
                return JsonResponse({'status': 'otp_required', 'message': 'OTP sent to your new email.'})

            if new_username != user.username:
                if user.username_changed:
                    return JsonResponse({'status': 'error', 'message': 'Username can only be changed once.'})
                user.username = new_username
                user.username_changed = True

            user.save()
            return JsonResponse({'status': 'success', 'message': 'Personal information updated successfully.'})

        elif 'update_password' in request.POST:
            current_password = request.POST.get('current-password')
            new_password = request.POST.get('new-password')
            confirm_password = request.POST.get('confirm-password')

            if new_password == confirm_password:
                if user.check_password(current_password):
                    user.set_password(new_password)
                    user.save()
                    update_session_auth_hash(request, user)
                    return JsonResponse({'status': 'success', 'message': 'Password updated successfully.'})
                else:
                    return JsonResponse({'status': 'error', 'message': 'Current password is incorrect.', 'error_type': 'current_password'})
            else:
                return JsonResponse({'status': 'error', 'message': 'New password and confirmation do not match.', 'error_type': 'password_mismatch'})

        elif 'delete_account' in request.POST:
            user.delete()
            return JsonResponse({'status': 'success', 'message': 'Account deleted successfully.', 'redirect_url': reverse('home')})

    return render(request, 'setting.html', {'user': user})

@login_required
def verify_email_otp(request):
    if request.method == 'POST':
        data = json.loads(request.body)  # Đọc dữ liệu từ request body
        otp = data.get('otp')  # Lấy mã OTP từ dữ liệu
        if otp == request.session.get('otp'):
            user = request.user
            user.email = request.session.get('new_email')
            user.save()
            del request.session['otp']
            del request.session['new_email']
            return JsonResponse({'success': True, 'message': 'Email updated successfully!'})
        return JsonResponse({'success': False})

@login_required
def resend_email_otp(request):
    if request.method == 'POST':
        otp = ''.join(random.choices('0123456789', k=6))
        request.session['otp'] = otp
        send_mail(
            'Your OTP Code',
            f'Your OTP code is {otp}',
            'from@example.com',
            [request.session.get('new_email')],
            fail_silently=False,
        )
        return JsonResponse({'success': True})

def delete_section(request, section_id):
    if request.method == 'POST':
        section = get_object_or_404(Section, id=section_id)
        section.delete()
        return JsonResponse({'success': True, 'message': 'Section deleted successfully.'})
    

def delete_submission(request, submission_id):
    if request.method == 'POST':
        submission = get_object_or_404(Submission, id=submission_id)
        submission.delete()
        return JsonResponse({'success': True, 'message': 'Submission deleted successfully.'})

@csrf_exempt
def delete_member(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        member_id = data.get('member_id')
        try:
            participant = Participant.objects.get(id=member_id)
            participant.delete()
            return JsonResponse({'success': True, 'message': 'Participant deleted successfully.'})
        except Participant.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Participant not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@csrf_exempt
def block_member(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        member_id = data.get('member_id')
        reason = data.get('reason', '') 
        try:
            participant = Participant.objects.get(id=member_id)
            BlockedParticipant.objects.create(user=participant.user, classroom=participant.classroom, reason=reason)
            participant.delete()
            return JsonResponse({'success': True, 'message': 'Participant blocked successfully.'})
        except Participant.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Participant not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def question_test_marking(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)
    quiz_results = submission.quiz_results.all()
    number_of_participants = quiz_results.filter(student__role='student').count()
    total_participants = submission.section.classroom.participants.filter(user__role='student').count()
    context = {
        'submission': submission,
        'quiz_results': quiz_results,
        'number_of_participants': number_of_participants,
        'total_participants': total_participants,
    }
    return render(request, 'question_test_marking.html', context)

def view_answer_history(request, quiz_result_id):
    quiz_result = get_object_or_404(QuizResult, id=quiz_result_id)
    answered_questions = quiz_result.answeredquestion_set.all()
    context = {
        'quiz_result': quiz_result,
        'answered_questions': answered_questions,
    }
    return render(request, 'view_answer_history.html', context)

def delete_quiz_result(request, quiz_result_id):
    if request.method == 'POST':
        quiz_result = get_object_or_404(QuizResult, id=quiz_result_id)
        quiz_result.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

def delete_assignment(request, assignment_id):
    if request.method == 'POST':
        assignment = get_object_or_404(StudentFile, id=assignment_id)
        assignment.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

def delete_account_admin(request, account_id):
    if request.method == 'POST':
        account = get_object_or_404(CustomUser, id=account_id)
        account.delete()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'failed'}, status=400)

@login_required
def adminPage(request):
    if not request.user.is_superuser:
        return redirect('home')
    
    # Data for select options in the form
    days = list(range(1, 32))
    months = {
        1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June',
        7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December'
    }
    years = list(range(1900, datetime.now().year + 1))  # Generates years from 1900 to current year

    # Context data
    statistical_data = []  # Add statistical data if applicable
    accounts = CustomUser.objects.all()
    subjects = Subjects.objects.all()
    subsection_files = SubsectionFile.objects.all()
    submission_files = SubmissionFile.objects.all()
    users = CustomUser.objects.all()

    context = {
        'statistical_data': statistical_data,
        'accounts': accounts,
        'subjects': subjects,
        'subsection_files': subsection_files,
        'submission_files': submission_files,
        'users': users,
        'notification_types': NotificationSystem.NOTIFICATION_TYPE_CHOICES,
        'days': days,  # Added list of days
        'months': months,  # Added dictionary of months
        'years': years,  # Added list of years
    }
    return render(request, 'adminPage.html', context)

@csrf_exempt
def create_account_admin(request):
    if request.method == 'POST':
        if 'update_account_data' in request.session:
            del request.session['update_account_data']
        data = json.loads(request.body)
        email = data.get('emailAdd')
        username = data.get('usernameAdd')
        day = data.get('day')
        month = data.get('month')
        year = data.get('year')
        role = data.get('role')
        grade = data.get('grade') if role == 'student' else None
        subject_id = data.get('subject') if role == 'teacher' else None
        password = data.get('passwordAdd')
        confirm_password = data.get('confirm-passwordAdd')

        errors = {}
        if not email:
            errors['emailAdd'] = 'Email is required.'
        elif CustomUser.objects.filter(email=email).exists():
            errors['emailAdd'] = 'Email is already in use.'

        if not username:
            errors['usernameAdd'] = 'Username is required.'
        elif CustomUser.objects.filter(username=username).exists():
            errors['usernameAdd'] = 'Username is already in use.'

        if not day or not month or not year:
            errors['date_of_birth'] = 'Date of birth is required.'
        else:
            try:
                date_of_birth = date(int(year), int(month), int(day))
            except ValueError:
                errors['date_of_birth'] = 'Invalid date of birth.'

        if not password:
            errors['passwordAdd'] = 'Password is required.'
        elif len(password) < 8:
            errors['passwordAdd'] = 'Password must be at least 8 characters long.'

        if password != confirm_password:
            errors['confirm-passwordAdd'] = 'Passwords do not match.'

        if errors:
            return JsonResponse({'status': 'error', 'errors': errors})

        # Store account data in session and send OTP
        otp = send_otp(email)
        request.session['otp'] = otp
        request.session['otp_expiry'] = (datetime.now() + timedelta(minutes=2)).isoformat()
        request.session['add_account_admin_data'] = {
            'username': username,
            'email': email,
            'password': password,
            'year': year,
            'month': month,
            'day': day,
            'role': role,
            'grade': grade,
            'subject': subject_id,
        }

        return JsonResponse({'status': 'otp_required', 'message': 'OTP has been sent to the provided email.'})


def update_account(request):
    if request.method == 'POST':
        if 'add_account_admin_data' in request.session:
            del request.session['add_account_admin_data']
        data = json.loads(request.body)
        account_id = data.get('id')
        account = get_object_or_404(CustomUser, id=account_id)

        new_username = data.get('usernameUpdate')
        new_email = data.get('emailUpdate')
        role = data.get('roleUpdate')
        grade = data.get('gradeUpdate') if role == 'student' else None
        subject_id = data.get('subjectUpdate') if role == 'teacher' else None

        errors = {}

        # Check for email changes and uniqueness
        if new_email != account.email and CustomUser.objects.filter(email=new_email).exists():
            errors['emailUpdate'] = 'Email is already in use.'

        # Check for username changes and uniqueness
        if new_username != account.username and CustomUser.objects.filter(username=new_username).exists():
            errors['usernameUpdate'] = 'Username is already in use.'

        if new_email == account.email and new_username == account.username:
            errors['emailUpdate'] = 'No changes made.'
            errors['usernameUpdate'] = 'No changes made.'
    
        if errors:
            return JsonResponse({'status': 'error', 'errors': errors})

        # Update account fields with new data
        account.username = new_username
        account.role = role

        if account.role == 'teacher':
            account.subject = Subjects.objects.get(id=subject_id) if subject_id else None
            account.grade = None
        elif account.role == 'student':
            account.grade = grade
            account.subject = None
        else:
            account.subject = None
            account.grade = None

        # Send OTP only if the email has changed
        if new_email != account.email:
            otp = send_otp(new_email)
            request.session['otp'] = otp
            request.session['otp_expiry'] = (datetime.now() + timedelta(minutes=2)).isoformat()
            request.session['update_account_data'] = {
                'id': account_id,
                'username': new_username,
                'email': new_email,
                'role': role,
                'grade': grade,
                'subject': subject_id,
            }
            return JsonResponse({'status': 'otp_required', 'message': 'OTP has been sent to the provided email.'})
        else:
            account.email = new_email
            account.save()
            return JsonResponse({'status': 'success', 'message': 'Account updated successfully.'})
    
def verify_otp_admin_combined(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        otp = data.get('otp')
        otp_expiry = request.session.get('otp_expiry')

        if not otp_expiry or datetime.now() > datetime.fromisoformat(otp_expiry):
            return JsonResponse({'status': 'error', 'message': 'OTP has expired. Please request a new one.'})

        if otp == request.session.get('otp'):
            # Determine if the OTP was for account creation or update
            if 'add_account_admin_data' in request.session:
                # Create new account
                account_data = request.session.get('add_account_admin_data', {})
                user = CustomUser.objects.create_user(
                    username=account_data['username'],
                    email=account_data['email'],
                    password=account_data['password'],
                    date_of_birth=date(
                        int(account_data['year']),
                        int(account_data['month']),
                        int(account_data['day'])
                    ),
                    role=account_data['role'],
                    grade=account_data['grade'],
                    terms_accepted=True,  # Assuming terms are accepted
                    subject=Subjects.objects.get(id=account_data['subject']) if account_data['subject'] else None
                )
                # Clean up session data
                del request.session['add_account_admin_data']

            elif 'update_account_data' in request.session:
                # Update existing account
                account_data = request.session.get('update_account_data', {})
                account = get_object_or_404(CustomUser, id=account_data['id'])

                # Update account fields with new data
                account.username = account_data['username']
                account.email = account_data['email']
                account.role = account_data['role']

                if account.role == 'teacher':
                    subject_id = account_data['subject']
                    account.subject = Subjects.objects.get(id=subject_id) if subject_id else None
                    account.grade = None
                elif account.role == 'student':
                    account.grade = account_data['grade']
                    account.subject = None
                else:
                    account.subject = None
                    account.grade = None

                account.save()
                # Clean up session data
                del request.session['update_account_data']

            # Clear shared OTP session data
            del request.session['otp']
            del request.session['otp_expiry']

            return JsonResponse({'status': 'success', 'message': 'Operation completed successfully.'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid OTP. Please try again.'})

def resend_otp_admin_combined(request):
    if request.method == 'POST':
        # Determine if we need to resend for add or update
        account_data = request.session.get('add_account_admin_data') or request.session.get('update_account_data')
        if account_data and 'email' in account_data:
            email = account_data['email']
            otp = send_otp(email)
            request.session['otp'] = otp
            request.session['otp_expiry'] = (datetime.now() + timedelta(minutes=2)).isoformat()
            return JsonResponse({'status': 'success', 'message': 'A new OTP has been sent.'})
        return JsonResponse({'status': 'error', 'message': 'No email found. Please try again.'})


from django.db.models import Sum, Max, Avg
from django.contrib.auth.decorators import login_required

@login_required
def achivement(request):
    user = request.user
    context = {}

    if user.role == 'teacher':
        classrooms_created = user.classrooms.count()
        total_likes = user.classrooms.aggregate(total_likes=Sum('likes'))['total_likes'] or 0
        average_rating = user.classrooms.aggregate(average_rating=Avg('average_rating'))['average_rating'] or 0.0

        context.update({
            'classrooms_created': classrooms_created,
            'total_likes': total_likes,
            'average_rating': average_rating,
        })

    elif user.role == 'student':
        classrooms_joined = user.participants.count()
        highest_score = user.student_files.aggregate(max_score=Max('score'))['max_score'] or 0.0
        total_correct_answers = user.quiz_results.aggregate(total_correct=Sum('correct_answers'))['total_correct'] or 0

        context.update({
            'classrooms_joined': classrooms_joined,
            'highest_score': highest_score,
            'total_correct_answers': total_correct_answers,
        })

    return render(request, 'achivement.html', context)

@login_required
def favorite(request):
    user = request.user
    status = request.GET.get('status', None)
    favorite_classrooms = FavoriteClassroom.objects.filter(user=user)
    public_classrooms = [fav.classroom for fav in favorite_classrooms if not fav.classroom.status]
    private_classrooms = [fav.classroom for fav in favorite_classrooms if fav.classroom.status]

    participant_classrooms = Participant.objects.filter(user=user).values_list('classroom_id', flat=True)
    co_teacher_requests = CoTeacherRequest.objects.filter(requester=user).values_list('classroom_id', flat=True)

    context = {
        'public_classrooms': public_classrooms,
        'private_classrooms': private_classrooms,
        'status': status,
        'participant_classrooms': participant_classrooms,
        'co_teacher_requests': co_teacher_requests,
    }
    return render(request, 'favorite.html', context)

@login_required
@csrf_exempt
def favorite_classroom(request, classroom_id):
    classroom = Classroom.objects.get(id=classroom_id)
    user = request.user
    favorite, created = FavoriteClassroom.objects.get_or_create(user=user, classroom=classroom)

    if not created:
        favorite.delete()
        classroom.likes = max(0, classroom.likes - 1)  # Đảm bảo likes không âm
        is_favorite = False
    else:
        classroom.likes += 1
        is_favorite = True

    classroom.save()

    return JsonResponse({'is_favorite': is_favorite})

def myclassroom(request):
    user = request.user
    participants = Participant.objects.filter(user=user)
    context = {
        'participants': participants,
        'subject': user.subject,
        'grade': user.grade,
        'status': request.GET.get('status')
    }
    return render(request, 'myclassroom.html', context)

def searchPage(request):
    query = request.GET.get('q', '')
    public_classrooms = Classroom.objects.filter(status=False, name__icontains=query) | Classroom.objects.filter(status=False, teacher__username__icontains=query)
    private_classrooms = Classroom.objects.filter(status=True, name__icontains=query) | Classroom.objects.filter(status=True, teacher__username__icontains=query)
    
    participant_classrooms = []
    if request.user.is_authenticated:
        participant_classrooms = Participant.objects.filter(user=request.user).values_list('classroom_id', flat=True)
    
    return render(request, 'searchPage.html', {
        'public_classrooms': public_classrooms,
        'private_classrooms': private_classrooms,
        'query': query,
        'participant_classrooms': participant_classrooms,
    })

from .models import Chatbot, CoTeacherRequest, ForumComment, ForumPost, NotificationSystem
from django.core.paginator import Paginator
def forum(request, classroom_id):
    user = request.user
    classroom = get_object_or_404(Classroom, id=classroom_id)
    
    questions = ForumPost.objects.filter(classroom=classroom, post_type='question', is_approved=True)
    discussions = ForumPost.objects.filter(classroom=classroom, post_type='discussion', is_approved=True)

    forum_posts = ForumPost.objects.filter(user=user, classroom=classroom)
    
    return render(request, 'forum.html', {
        'classroom': classroom,
        'questions': questions,
        'discussions': discussions,
        'forum_posts': forum_posts,
    })

def forum_detail(request, post_id):
    post = get_object_or_404(ForumPost, id=post_id)
    comments = post.forum_comments.all()
    if request.user not in post.views_by.all(): 
        post.views += 1
        post.views_by.add(request.user)
        post.save()
    return render(request, 'forum_detail.html', {'post': post, 'comments': comments})


def add_comment(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(ForumPost, id=post_id)
        comment_text = request.POST.get('comment')
        if comment_text:
            ForumComment.objects.create(user=request.user, post=post, text=comment_text)
            return JsonResponse({'status': 'success', 'message': 'Comment added successfully!', 'scroll': True})
        else:
            return JsonResponse({'status': 'error', 'message': 'Please provide a comment.'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})

def create_post(request, classroom_id):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        post_type = request.POST.get('post_type')  # 'question' hoặc 'discussion'
        classroom = get_object_or_404(Classroom, id=classroom_id)
        
        if not title or not content or not post_type:
            return JsonResponse({'status': 'error', 'message': 'All fields are required.'})
        
        ForumPost.objects.create(
            title=title,
            content=content,
            post_type=post_type,
            classroom=classroom,
            user=request.user,
            is_approved=True if request.user.id == classroom.teacher.id else False
        )
        return JsonResponse({'status': 'success', 'message': 'Post created successfully!', 'redirect_url': reverse('manage_posts', args=[classroom_id])})
    
    return render(request, 'create_post.html', {'classroom_id': classroom_id})

def manage_posts(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id)
    posts = ForumPost.objects.filter(classroom=classroom, user=request.user)
    return render(request, 'manage_posts.html', {'posts': posts, 'classroom_id': classroom_id, 'classroom': classroom})

from django.views.decorators.http import require_POST
@require_POST
def edit_post(request, post_id):
    post = get_object_or_404(ForumPost, id=post_id, user=request.user)
    title = request.POST.get('title')
    content = request.POST.get('content')
    post_type = request.POST.get('post_type') 


    if title and content:
        post.title = title
        post.content = content
        post.post_type = post_type
        post.save()
        # Trả về JSONResponse để xử lý modal thông báo thành công
        return JsonResponse({'status': 'success', 'message': 'Post updated successfully.'})
    
    # Trả về JSONResponse nếu có lỗi
    return JsonResponse({'status': 'error', 'message': 'Failed to update the post. Title and Content are required.'})

@require_POST
def delete_post(request, post_id):
    post = get_object_or_404(ForumPost, id=post_id, user=request.user)
    post.delete()
    # Trả về JSONResponse để xử lý modal thông báo thành công
    return JsonResponse({'status': 'success', 'message': 'Post deleted successfully.'})
    
def manage_approve_posts(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id)
    posts = ForumPost.objects.filter(classroom=classroom)
    return render(request, 'approve_posts.html', {'posts': posts, 'classroom_id': classroom_id, 'classroom': classroom})

def approve_post(request, post_id):
    post = get_object_or_404(ForumPost, id=post_id)
    if request.method == 'POST':
        post.is_approved = True
        post.is_rejected = False
        post.save()
        
        # Gửi mail thông báo
        subject = 'Your post has been approved'
        message = f'Hi {post.user.username},\n\nYour post titled "{post.title}" has been approved.\n\nBest regards,\nYour Classroom Team'
        recipient_list = [post.user.email]
        send_mail(subject, message, 'no-reply@classroom.com', recipient_list)
        
        return JsonResponse({'status': 'success', 'message': 'Post approved successfully.'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)

def reject_post(request, post_id):
    post = get_object_or_404(ForumPost, id=post_id)
    if request.method == 'POST':
        reason = request.POST.get('reason')
        post.reason = reason
        post.is_rejected = True
        post.is_approved = False
        post.save()
        
        subject = 'Your post has been rejected'
        message = f'Hi {post.user.username},\n\nYour post titled "{post.title}" has been rejected for the following reason:\n\n{reason}\n\nBest regards,\nYour Classroom Team'
        recipient_list = [post.user.email]
        send_mail(subject, message, 'no-reply@classroom.com', recipient_list)
        
        return JsonResponse({'status': 'success', 'message': 'Post rejected successfully.'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)

@require_POST
def toggle_like(request, post_id):
    post = get_object_or_404(ForumPost, id=post_id)
    user = request.user
    if user in post.liked_by.all():
        post.liked_by.remove(user)
        post.likes -= 1
        message = 'Post unliked successfully.'
    else:
        post.liked_by.add(user)
        post.likes += 1
        message = 'Post liked successfully.'
    post.save()
    return JsonResponse({'status': 'success', 'likes': post.likes, 'message': message})

def notification(request):
    user_notifications = NotificationSystem.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'notification.html', {'notifications': user_notifications})

@csrf_exempt
def delete_notification(request, notification_id):
    if request.method == 'POST':
        notification = get_object_or_404(NotificationSystem, id=notification_id)
        notification.delete()
        return JsonResponse({'status': 'success', 'message': 'Notification deleted successfully.'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})

def mark_notification_as_read(request, notification_id):
    if request.method == 'POST':
        try:
            notification = NotificationSystem.objects.get(id=notification_id, user=request.user)
            notification.is_read = True
            notification.save()
            return JsonResponse({'status': 'success'})
        except NotificationSystem.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Notification not found'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

def get_unread_notification_count(request):
    if request.user.is_authenticated:
        unread_count = NotificationSystem.objects.filter(user=request.user, is_read=False).count()
        return JsonResponse({'unread_count': unread_count})
    return JsonResponse({'unread_count': 0})

@csrf_exempt
def delete_all_notifications(request):
    if request.method == 'POST':
        NotificationSystem.objects.filter(user=request.user).delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
def create_notification(request):
    if request.method == 'POST':
        user_id = request.POST.get('user')
        notification_type = request.POST.get('type')
        title = request.POST.get('title', 'Notification')
        text = request.POST.get('text')

        if not text:
            return JsonResponse({'status': 'error', 'message': 'Please enter the notification content.'})

        channel_layer = get_channel_layer()

        if user_id == 'all':
            users = CustomUser.objects.exclude(id=request.user.id)
            for user in users:
                notification = NotificationSystem.objects.create(
                    user=user,
                    title=title if title else 'Notification',
                    text=text,
                    type=notification_type
                )

                async_to_sync(channel_layer.group_send)(
                    f'notifications_{user.username}',
                    {
                        'type': 'send_notification',
                        'notification': {
                            'id': notification.id,
                            'title': notification.title if notification.title else 'Notification',
                            'text': notification.text,
                            'type': notification.get_type_display(),
                            'created_at': (notification.created_at + timedelta(hours=7)).strftime("%H:%M %p · %d/%m/%Y"),
                            'is_read': notification.is_read
                        }
                    }
                )
            return JsonResponse({'status': 'success', 'message': 'Notification sent to all users.'})
        else:
            user = CustomUser.objects.filter(id=user_id).exclude(id=request.user.id).first()
            if user:
                notification = NotificationSystem.objects.create(
                    user=user,
                    title=title if title else 'Notification',
                    text=text,
                    type=notification_type
                )

                async_to_sync(channel_layer.group_send)(
                    f'notifications_{user.username}',
                    {
                        'type': 'send_notification',
                        'notification': {
                            'id': notification.id,
                            'title': notification.title if notification.title else 'Notification',
                            'text': notification.text,
                            'type': notification.get_type_display(),
                            'created_at': (notification.created_at + timedelta(hours=7)).strftime("%H:%M %p · %d/%m/%Y"),
                            'is_read': notification.is_read
                        }
                    }
                )
                return JsonResponse({'status': 'success', 'message': 'Notification sent.'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid user.'})
    else:
        users = CustomUser.objects.all().exclude(id=request.user.id)
        return render(request, 'create_notification.html', {'users': users})








