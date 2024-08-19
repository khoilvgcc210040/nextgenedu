from .models import AcademicYear

def academic_years_processor(request):
    academic_years = AcademicYear.objects.all()
    return {'academic_years': academic_years}


def query_params_context_processor(request):
    return {
        'errors': request.GET.getlist('errors', []),
        'name': request.GET.get('name', ''),
        'description': request.GET.get('description', ''),
        'school': request.GET.get('school', ''),
        'academic_year_id': request.GET.get('academic_year_id', ''),
        'status': request.GET.get('status', 'public'),
        'password': request.GET.get('password', '')
    }

