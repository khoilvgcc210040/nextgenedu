from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import ForumPost, ForumComment, AnsweredQuestion, BlockedParticipant, FavoriteClassroom, ChatMessage, Comment, CustomUser, Subjects, Classroom, AcademicYear, Section, Submission, StudentFile, Participant, Question, Answer, SubsectionFile, SubmissionFile, QuizResult

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'first_name', 'last_name', 'subject', 'grade', 'role', 'is_staff')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'date_of_birth', 'role', 'subject', 'grade', 'terms_accepted', 'notify_sections', 'username_changed')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Subjects)
admin.site.register(Classroom)
admin.site.register(AcademicYear)
admin.site.register(Section)
admin.site.register(Submission)
admin.site.register(Participant)
admin.site.register(StudentFile)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(SubmissionFile)
admin.site.register(SubsectionFile)
admin.site.register(QuizResult)
admin.site.register(Comment)
admin.site.register(ChatMessage)
admin.site.register(FavoriteClassroom)
admin.site.register(AnsweredQuestion)
admin.site.register(BlockedParticipant)
admin.site.register(ForumPost)
admin.site.register(ForumComment)

