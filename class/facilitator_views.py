"""
Facilitator Student Management Views
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from .models import School, ClassSection, Student, Enrollment, FacilitatorSchool, User
from .mixins import FacilitatorAccessMixin
from .decorators import facilitator_required
from .forms import AddUserForm  # We'll need to create a student form


class FacilitatorSchoolListView(FacilitatorAccessMixin, ListView):
    """
    View for facilitators to see their assigned schools
    """
    model = School
    template_name = 'facilitator/schools/list.html'
    context_object_name = 'schools'
    
    def get_queryset(self):
        """Return only schools assigned to the current facilitator, ordered alphabetically"""
        return self.get_facilitator_schools().order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add enrollment counts for each school
        schools_with_counts = []
        for school in context['schools']:
            enrollment_count = Enrollment.objects.filter(
                school=school,
                is_active=True
            ).count()
            
            class_count = ClassSection.objects.filter(
                school=school,
                is_active=True
            ).count()
            
            schools_with_counts.append({
                'school': school,
                'enrollment_count': enrollment_count,
                'class_count': class_count
            })
        
        context['schools_with_counts'] = schools_with_counts
        return context


class FacilitatorSchoolDetailView(FacilitatorAccessMixin, DetailView):
    """
    View for facilitators to see classes within their assigned school
    """
    model = School
    template_name = 'facilitator/schools/detail.html'
    context_object_name = 'school'
    
    def get_object(self, queryset=None):
        """Get school and verify facilitator has access"""
        school = super().get_object(queryset)
        self.verify_school_access_or_403(school.id)
        return school
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        school = self.object
        
        # Get all classes for this school
        classes = ClassSection.objects.filter(
            school=school,
            is_active=True
        ).order_by('class_level', 'section')
        
        # Add enrollment counts for each class
        classes_with_counts = []
        for class_section in classes:
            enrollment_count = Enrollment.objects.filter(
                class_section=class_section,
                is_active=True
            ).count()
            
            classes_with_counts.append({
                'class_section': class_section,
                'enrollment_count': enrollment_count
            })
        
        context['classes_with_counts'] = classes_with_counts
        
        # Add filtering options
        grade_levels = classes.values_list('class_level', flat=True).distinct()
        context['grade_levels'] = sorted(set(grade_levels))
        
        # Apply filters if provided
        grade_filter = self.request.GET.get('grade')
        if grade_filter:
            classes_with_counts = [
                item for item in classes_with_counts 
                if item['class_section'].class_level == grade_filter
            ]
            context['selected_grade'] = grade_filter
        
        context['filtered_classes'] = classes_with_counts
        return context


class FacilitatorStudentListView(FacilitatorAccessMixin, ListView):
    """
    View for facilitators to see students from their assigned schools
    """
    model = Enrollment
    template_name = 'facilitator/students/list.html'
    context_object_name = 'enrollments'
    paginate_by = 20
    
    def get_queryset(self):
        """Return students from facilitator's assigned schools"""
        queryset = Enrollment.objects.filter(
            is_active=True,
            school__in=self.get_facilitator_schools()
        ).select_related('student', 'class_section', 'school').order_by('student__full_name')
        
        # Apply filters
        school_filter = self.request.GET.get('school')
        class_filter = self.request.GET.get('class')
        grade_filter = self.request.GET.get('grade')
        search_query = self.request.GET.get('search')
        
        if school_filter:
            queryset = queryset.filter(school_id=school_filter)
        
        if class_filter:
            queryset = queryset.filter(class_section_id=class_filter)
        
        if grade_filter:
            queryset = queryset.filter(class_section__class_level=grade_filter)
        
        if search_query:
            queryset = queryset.filter(
                Q(student__full_name__icontains=search_query) |
                Q(student__enrollment_number__icontains=search_query)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add filter options
        context['schools'] = self.get_facilitator_schools()
        
        # Get classes from assigned schools
        context['classes'] = self.get_assigned_class_sections()
        
        # Get unique grade levels
        grade_levels = ClassSection.objects.filter(
            school__in=self.get_facilitator_schools()
        ).values_list('class_level', flat=True).distinct()
        context['grade_levels'] = sorted(set(grade_levels))
        
        # Preserve filter values
        context['filters'] = {
            'school': self.request.GET.get('school', ''),
            'class': self.request.GET.get('class', ''),
            'grade': self.request.GET.get('grade', ''),
            'search': self.request.GET.get('search', ''),
        }
        
        return context


class FacilitatorStudentCreateView(FacilitatorAccessMixin, CreateView):
    """
    View for facilitators to create new students
    """
    model = Student
    template_name = 'facilitator/students/create.html'
    fields = ['enrollment_number', 'full_name', 'gender']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Only show classes from facilitator's assigned schools
        context['class_sections'] = self.get_assigned_class_sections()
        context['schools'] = self.get_facilitator_schools()
        
        return context
    
    def form_valid(self, form):
        """Create student and enrollment"""
        # Get the selected class section
        class_section_id = self.request.POST.get('class_section')
        if not class_section_id:
            messages.error(self.request, "Please select a class section.")
            return self.form_invalid(form)
        
        # Verify facilitator has access to this class
        self.verify_class_access_or_403(class_section_id)
        
        class_section = get_object_or_404(ClassSection, id=class_section_id)
        
        # Save the student
        student = form.save()
        
        # Create enrollment
        Enrollment.objects.create(
            student=student,
            school=class_section.school,
            class_section=class_section,
            is_active=True
        )
        
        messages.success(self.request, f"Student {student.full_name} created successfully!")
        return redirect('facilitator_students_list')


class FacilitatorStudentUpdateView(FacilitatorAccessMixin, UpdateView):
    """
    View for facilitators to edit existing students
    """
    model = Student
    template_name = 'facilitator/students/edit.html'
    fields = ['enrollment_number', 'full_name', 'gender']
    
    def get_object(self, queryset=None):
        """Get student and verify facilitator has access"""
        student = super().get_object(queryset)
        
        # Check if student is enrolled in any of facilitator's schools
        enrollment = Enrollment.objects.filter(
            student=student,
            is_active=True,
            school__in=self.get_facilitator_schools()
        ).first()
        
        if not enrollment:
            raise PermissionDenied("You do not have access to this student.")
        
        return student
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get current enrollment
        student = self.object
        current_enrollment = Enrollment.objects.filter(
            student=student,
            is_active=True,
            school__in=self.get_facilitator_schools()
        ).first()
        
        context['current_enrollment'] = current_enrollment
        context['class_sections'] = self.get_assigned_class_sections()
        context['schools'] = self.get_facilitator_schools()
        
        return context
    
    def form_valid(self, form):
        """Update student and enrollment if class changed"""
        student = form.save()
        
        # Check if class section was changed
        new_class_section_id = self.request.POST.get('class_section')
        if new_class_section_id:
            # Verify facilitator has access to new class
            self.verify_class_access_or_403(new_class_section_id)
            
            new_class_section = get_object_or_404(ClassSection, id=new_class_section_id)
            
            # Update enrollment
            current_enrollment = Enrollment.objects.filter(
                student=student,
                is_active=True,
                school__in=self.get_facilitator_schools()
            ).first()
            
            if current_enrollment:
                current_enrollment.class_section = new_class_section
                current_enrollment.school = new_class_section.school
                current_enrollment.save()
        
        messages.success(self.request, f"Student {student.full_name} updated successfully!")
        return redirect('facilitator_students_list')


# Function-based views for AJAX endpoints
@facilitator_required
def facilitator_ajax_school_classes(request):
    """AJAX endpoint to get classes for a specific school"""
    school_id = request.GET.get('school_id')
    if not school_id:
        return JsonResponse({'error': 'School ID required'}, status=400)
    
    # Create mixin instance to check access
    mixin = FacilitatorAccessMixin()
    mixin.request = request
    
    if not mixin.check_school_access(school_id):
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    classes = ClassSection.objects.filter(
        school_id=school_id,
        is_active=True
    ).values('id', 'class_level', 'section', 'display_name').order_by('class_level', 'section')
    
    return JsonResponse({'classes': list(classes)})


@facilitator_required
def facilitator_student_detail(request, student_id):
    """View student details and attendance"""
    student = get_object_or_404(Student, id=student_id)
    
    # Create mixin instance to check access
    mixin = FacilitatorAccessMixin()
    mixin.request = request
    
    # Check if student is in facilitator's schools
    enrollment = Enrollment.objects.filter(
        student=student,
        is_active=True,
        school__in=mixin.get_facilitator_schools()
    ).first()
    
    if not enrollment:
        messages.error(request, "You do not have access to this student.")
        return redirect('facilitator_students_list')
    
    # Get attendance statistics
    from .models import Attendance, ActualSession
    
    total_sessions = ActualSession.objects.filter(
        planned_session__class_section=enrollment.class_section,
        status='conducted'
    ).count()
    
    present_count = Attendance.objects.filter(
        enrollment=enrollment,
        status='present'
    ).count()
    
    absent_count = Attendance.objects.filter(
        enrollment=enrollment,
        status='absent'
    ).count()
    
    attendance_percentage = (present_count / total_sessions * 100) if total_sessions > 0 else 0
    
    # Get recent attendance records
    recent_attendance = Attendance.objects.filter(
        enrollment=enrollment
    ).select_related('actual_session__planned_session').order_by('-actual_session__date')[:10]
    
    context = {
        'student': student,
        'enrollment': enrollment,
        'stats': {
            'total_sessions': total_sessions,
            'present_count': present_count,
            'absent_count': absent_count,
            'attendance_percentage': round(attendance_percentage, 1)
        },
        'recent_attendance': recent_attendance
    }
    
    return render(request, 'facilitator/students/detail.html', context)