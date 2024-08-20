from datetime import date, timedelta, timezone
from django.db.models import Avg
from urllib.parse import urlencode
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.urls import reverse
from home.models import AcademicYear, Answer, Classroom, Comment, CustomUser, Participant, Question, QuizResult, Section, StudentFile, Subjects, Submission, SubmissionFile, SubsectionFile

from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.forms import SetPasswordForm
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now

User = get_user_model()

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
            subject = None
            grade = None
            if role == 'teacher':
                subject_id = request.POST.get('subject')
                if subject_id:
                    subject = Subjects.objects.get(id=subject_id)
                    grade = subject.grade 
            elif role == 'student':
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
                    'subject': subject_id if subject else None,
                    'grade': grade,
                    'terms': terms
                }
                return redirect('/auth/?form=signup&signup_error=True')
            else:
                user = CustomUser.objects.create_user(username=username, email=email, password=password)
                user.date_of_birth = date(year, month, day)
                user.role = role
                user.grade = grade if grade else ''
                user.terms_accepted = terms
                user.subject = subject.name if subject else None
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
        subjects = Subjects.objects.all()
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
            'selected_subject_id': signup_data.get('subject', None),
            'terms': signup_data.get('terms', False),
            'subjects': subjects,
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
                logger.debug(f'Generated uidb64: {uidb64}') 
                c = {
                    "email": user.email,
                    'domain': 'localhost:8000', 
                    'site_name': 'Website',
                    "uidb64": uidb64,  
                    "user": user,
                    'token': default_token_generator.make_token(user),
                    'protocol': 'http',
                }
                email = render_to_string(email_template_name, c)
                send_mail(subject, email, 'NextGenEdu <nextgenedu03.info@gmail.com>', [user.email], fail_silently=False)
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
                    return redirect('reset_password')
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

        name = request.POST['name']
        description = request.POST['description']
        school = request.POST['school']
        academic_year_id = request.POST['academic_year']
        academic_year = AcademicYear.objects.get(id=academic_year_id)

        teacher = request.user
        grade = teacher.grade
        subject = teacher.subject
        status = request.POST.get('status', 'public')
        password = request.POST.get('classroom_password', '')
        next_template = request.POST.get('next_template', request.resolver_match.view_name)

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

            section = Section.objects.create(
                classroom=classroom,
                title="Welcome",
            )
            section.save()

            Participant.objects.create(user=request.user, classroom=classroom)

            return redirect('manage_classroom_detail', id=classroom.id)

        except ValidationError as e:
            errors.extend(e.messages)

        except IntegrityError:
            errors.append('Classroom with this name already exists for this teacher.')

        if errors:
            query_params = {
                'errors': errors,
                'name': name,
                'description': description,
                'school': school,
                'academic_year_id': academic_year_id,
                'status': status,
                'password': password
            }
            url = reverse(next_template) + '?' + urlencode(query_params, doseq=True)
            return HttpResponseRedirect(url)

    return redirect('home')


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


def classrooms(request, subject_id, grade):
    subject = get_object_or_404(Subjects, id=subject_id, grade=grade)
    status = request.GET.get('status', None)

    if status is not None:
        classrooms = Classroom.objects.filter(subject=subject, grade=grade, status=status)
    else:
        classrooms = Classroom.objects.filter(subject=subject, grade=grade)

    context = {
        'subject': subject,
        'grade': grade,
        'classrooms': classrooms,
        'status': status,
    }
    return render(request, 'classrooms.html', context)

def enter_password(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id)
    
    if request.method == 'POST':
        entered_password = request.POST.get('password')
        if entered_password == classroom.password:
            participant_exists = Participant.objects.filter(user=request.user, classroom=classroom).exists()
            
            if not participant_exists:
                Participant.objects.create(user=request.user, classroom=classroom)
                
            return redirect('classroom_detail', id=classroom.id)
        else:
            return HttpResponse("Incorrect password")

    return redirect('classrooms', subject_id=classroom.subject.id, grade=classroom.grade)


@login_required
def classroom_detail(request, id):
    classroom = get_object_or_404(Classroom, id=id)
    sections = Section.objects.filter(classroom=classroom)
    participants = classroom.participants.all()

    scores_data = []
    for participant in participants:
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
        })

    # Sort by total_score and total_time for ranking purposes
    scores_data.sort(key=lambda x: (-x['total_score'], x['total_time']))

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
    }
    return render(request, 'classroom_detail.html', context)


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

def take_quiz(request, submission_id, question_id):
    submission = get_object_or_404(Submission, id=submission_id)
    question = get_object_or_404(Question, id=question_id)

    total_questions = submission.questions.count()

    # Lấy số lượng câu hỏi đã được trả lời
    quiz_result, created = QuizResult.objects.get_or_create(
        submission=submission,
        student=request.user,
        defaults={'correct_answers': 0, 'total_questions': total_questions, 'score': 0.0}
    )
    answered_questions = quiz_result.answered_questions

    # Lấy thời gian đã trôi qua nếu đã lưu trước đó
    elapsed_time = quiz_result.time_taken.total_seconds() if quiz_result.time_taken else 0

    return render(request, 'take_quiz.html', {
        'submission': submission,
        'current_question': question,
        'total_questions': total_questions,
        'answered_questions': answered_questions,
        'elapsed_time': elapsed_time  # Truyền elapsed_time vào template
    })


def submit_answer(request, submission_id, question_id):
    submission = get_object_or_404(Submission, id=submission_id)
    question = get_object_or_404(Question, id=question_id)
    selected_answer_id = request.POST.get('selected_answer')
    selected_answer = get_object_or_404(Answer, id=selected_answer_id)

    # Kiểm tra câu trả lời đúng hay sai
    correct = selected_answer.is_correct

    # Cập nhật hoặc tạo mới QuizResult nếu chưa có
    quiz_result, created = QuizResult.objects.get_or_create(
        submission=submission,
        student=request.user,
        defaults={'correct_answers': 0, 'total_questions': submission.questions.count(), 'score': 0.0}
    )
    
    if correct:
        quiz_result.correct_answers += 1
     
    quiz_result.answered_questions += 1
    
    # Tính toán điểm
    quiz_result.total_questions = submission.questions.count()
    quiz_result.score = (quiz_result.correct_answers / quiz_result.total_questions) * 10

    # Lấy thời gian đã trôi qua (elapsed_time)
    elapsed_time = int(request.POST.get('elapsed_time', '0'))

    # Nếu là câu hỏi cuối cùng, lưu lại tổng thời gian làm bài
    next_question = Question.objects.filter(submission=submission, id__gt=question_id).first()
    if next_question:
        # Chuyển đến câu hỏi tiếp theo, truyền elapsed_time để tiếp tục đếm
        quiz_result.time_taken = timedelta(seconds=elapsed_time)
        quiz_result.save()
        return redirect('take_quiz', submission_id=submission.id, question_id=next_question.id)
    else:
        # Đây là câu hỏi cuối cùng, lưu thời gian tổng
        quiz_result.time_taken = timedelta(seconds=elapsed_time)
        quiz_result.save()
        return redirect('quiz_result', submission_id=submission.id)


def quiz_result(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)
    classroom = submission.section.classroom

    # Lấy kết quả bài kiểm tra của học sinh hiện tại
    quiz_result = get_object_or_404(QuizResult, submission=submission, student=request.user)

    # Chuyển hướng về trang classroom_detail và truyền các tham số cần thiết qua URL
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
    context = {
        'classroom': classroom
    }
    return render(request, 'setting_classroom.html', context)

def manage_classroom_detail(request, id):
    classroom = get_object_or_404(Classroom, id=id)
    sections = classroom.sections.all()
    participants = classroom.participants.all()
    assignments = Submission.objects.filter(section__classroom=classroom, submission_type='assignment').prefetch_related('student_files')
    num_sections = sections.count()
    num_participants = participants.count()
    context = {
        'classroom': classroom,
        'sections': sections,
        'participants': participants,
        'assignments': assignments,
        'num_sections': num_sections,
        'num_participants': num_participants,
    }
    return render(request, 'manage_classroom_detail.html', context)

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
            if section_type == 'sub' and parent_section_id:
                parent_section = get_object_or_404(Section, id=parent_section_id)
            
            section = Section.objects.create(
                classroom=classroom,
                title=title,
                description=description,
                parent_section=parent_section
            )
            section.save()
            messages.success(request, 'Section/Subsection created successfully!')

        elif action_type == 'submission':
            submission_type = request.POST.get('submission_type')
            open_date = request.POST.get('open_date')
            close_date = request.POST.get('close_date')
            section = get_object_or_404(Section, id=request.POST.get('parent_section'))
            
            submission = Submission.objects.create(
                section=section,
                title=title,
                submission_type=submission_type,
                description=description,
                open_date=open_date,
                close_date=close_date
            )
            submission.save()
            messages.success(request, 'Submission created successfully!')

        return redirect('manage_classroom_detail', id=classroom.id)

    return redirect('home')



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
    
    context = {
        'submission': submission,
        'questions': questions,
    }
    
    return render(request, 'question_list.html', context)

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


def marking(request, assignment_id):
    assignment = get_object_or_404(Submission, id=assignment_id)
    student_files = assignment.student_files.all()

    total_participants = assignment.section.classroom.participants.count()
    submitted_participants = student_files.values('student').distinct().count()

    show_modal = False
    show_success_message = False
    student_file_to_mark = None

    if request.method == 'POST':
        student_file_id = request.POST.get('student_file_id')
        score = request.POST.get('score')

        if student_file_id and score:
            try:
                score = float(score)
                if 0 <= score <= 10:
                    student_file = get_object_or_404(StudentFile, id=student_file_id)
                    student_file.score = score
                    student_file.save()
                    show_success_message = True
                else:
                    messages.error(request, 'Score must be between 0 and 10.')
                    show_modal = True
                    student_file_to_mark = student_file_id
            except ValueError:
                messages.error(request, 'Invalid score. Please enter a number.')
                show_modal = True
                student_file_to_mark = student_file_id
        else:
            messages.error(request, 'All fields are required.')
            show_modal = True
            student_file_to_mark = student_file_id

        if not show_modal and show_success_message:
            return redirect('marking', assignment_id=assignment.id)

    context = {
        'assignment': assignment,
        'student_files': student_files,
        'total_participants': total_participants,
        'submitted_participants': submitted_participants,
        'show_modal': show_modal,
        'student_file_to_mark': student_file_to_mark,
    }

    return render(request, 'marking.html', context)


def setting(request):
    # classroom = get_object_or_404(Classroom, id=id)
    # context = {
    #     'classroom': classroom
    # }
    return render(request, 'setting.html')

def adminPage(request):
    # classroom = get_object_or_404(Classroom, id=id)
    # context = {
    #     'classroom': classroom
    # }
    return render(request, 'adminPage.html')

def achivement(request):
    # classroom = get_object_or_404(Classroom, id=id)
    # context = {
    #     'classroom': classroom
    # }
    return render(request, 'achivement.html')

def favorite(request):
    # classroom = get_object_or_404(Classroom, id=id)
    # context = {
    #     'classroom': classroom
    # }
    return render(request, 'favorite.html')

def myclassroom(request):
    # classroom = get_object_or_404(Classroom, id=id)
    # context = {
    #     'classroom': classroom
    # }
    return render(request, 'myclassroom.html')




