from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import ActualSession, FacilitatorTask, CurriculumSession, CurriculumStatus
from .decorators import facilitator_required
import os
import logging

logger = logging.getLogger(__name__)


@facilitator_required
def facilitator_task_step(request, actual_session_id):
    """
    Facilitator task/preparation step
    Options: Take photo, Take video, Upload Facebook link
    Also displays lesson plan content for the session
    """
    from .models import CurriculumSession
    
    actual_session = get_object_or_404(ActualSession, id=actual_session_id)
    
    # Verify facilitator access
    if actual_session.planned_session.class_section.school.facilitators.filter(
        facilitator=request.user,
        is_active=True
    ).count() == 0:
        messages.error(request, "You don't have access to this session")
        return redirect('facilitator_today_session')
    
    # Get existing tasks
    existing_tasks = FacilitatorTask.objects.filter(
        actual_session=actual_session,
        facilitator=request.user
    )
    
    # Get lesson plan content from CurriculumSession
    planned_session = actual_session.planned_session
    curriculum_session = None
    
    try:
        # Try to find matching CurriculumSession by day_number
        # Assuming curriculum is language-specific, try to match by day
        curriculum_session = CurriculumSession.objects.filter(
            day_number=planned_session.day_number,
            status=CurriculumStatus.PUBLISHED
        ).first()
    except Exception as e:
        logger.warning(f"Error loading curriculum session: {str(e)}")
    
    # Check if this is a grouped session
    is_grouped_session = planned_session.grouped_session_id is not None
    grouped_classes = []
    
    if is_grouped_session:
        # Get all classes in the group
        grouped_sessions = PlannedSession.objects.filter(
            grouped_session_id=planned_session.grouped_session_id,
            day_number=planned_session.day_number
        ).select_related('class_section')
        grouped_classes = [gs.class_section for gs in grouped_sessions]
    
    context = {
        'actual_session': actual_session,
        'planned_session': planned_session,
        'existing_tasks': existing_tasks,
        'curriculum_session': curriculum_session,
        'is_grouped_session': is_grouped_session,
        'grouped_classes': grouped_classes,
        'task_count': existing_tasks.count(),
    }
    
    return render(request, 'facilitator/facilitator_task.html', context)


@facilitator_required
@require_http_methods(["POST"])
def facilitator_task_upload_photo(request, actual_session_id=None):
    """
    Upload photo for facilitator task
    actual_session_id is optional - if not provided, task is created without session link
    """
    try:
        actual_session = None
        if actual_session_id:
            actual_session = get_object_or_404(ActualSession, id=actual_session_id)
        
        if 'photo' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No photo provided'}, status=400)
        
        photo = request.FILES['photo']
        
        # Validate file type
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
        ext = os.path.splitext(photo.name)[1].lower()
        if ext not in valid_extensions:
            return JsonResponse({'success': False, 'error': 'Invalid file type. Use JPG, PNG, or GIF'}, status=400)
        
        # Create task
        task = FacilitatorTask.objects.create(
            actual_session=actual_session,
            facilitator=request.user,
            media_type='photo',
            media_file=photo,
            description=request.POST.get('description', '')
        )
        
        return JsonResponse({
            'success': True,
            'task_id': str(task.id),
            'message': 'Photo uploaded successfully'
        })
    except Exception as e:
        logger.error(f"Error uploading photo: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@facilitator_required
@require_http_methods(["POST"])
def facilitator_task_upload_video(request, actual_session_id=None):
    """
    Upload video for facilitator task
    actual_session_id is optional - if not provided, task is created without session link
    """
    try:
        actual_session = None
        if actual_session_id:
            actual_session = get_object_or_404(ActualSession, id=actual_session_id)
        
        if 'video' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No video provided'}, status=400)
        
        video = request.FILES['video']
        
        # Validate file type
        valid_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
        ext = os.path.splitext(video.name)[1].lower()
        if ext not in valid_extensions:
            return JsonResponse({'success': False, 'error': 'Invalid file type. Use MP4, AVI, MOV, MKV, or WebM'}, status=400)
        
        # Create task
        task = FacilitatorTask.objects.create(
            actual_session=actual_session,
            facilitator=request.user,
            media_type='video',
            media_file=video,
            description=request.POST.get('description', '')
        )
        
        return JsonResponse({
            'success': True,
            'task_id': str(task.id),
            'message': 'Video uploaded successfully'
        })
    except Exception as e:
        logger.error(f"Error uploading video: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@facilitator_required
@require_http_methods(["POST"])
def facilitator_task_facebook_link(request, actual_session_id=None):
    """
    Add Facebook link for facilitator task
    actual_session_id is optional - if not provided, task is created without session link
    """
    try:
        actual_session = None
        if actual_session_id:
            actual_session = get_object_or_404(ActualSession, id=actual_session_id)
        
        facebook_link = request.POST.get('facebook_link', '').strip()
        
        if not facebook_link:
            return JsonResponse({'success': False, 'error': 'Facebook link is required'}, status=400)
        
        # Validate Facebook URL
        if 'facebook.com' not in facebook_link and 'fb.watch' not in facebook_link:
            return JsonResponse({'success': False, 'error': 'Invalid Facebook link'}, status=400)
        
        # Create task
        task = FacilitatorTask.objects.create(
            actual_session=actual_session,
            facilitator=request.user,
            media_type='facebook_link',
            facebook_link=facebook_link,
            description=request.POST.get('description', '')
        )
        
        return JsonResponse({
            'success': True,
            'task_id': str(task.id),
            'message': 'Facebook link added successfully'
        })
    except Exception as e:
        logger.error(f"Error adding Facebook link: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@facilitator_required
@require_http_methods(["POST"])
def facilitator_task_delete(request, task_id):
    """
    Delete facilitator task
    """
    task = get_object_or_404(FacilitatorTask, id=task_id, facilitator=request.user)
    actual_session_id = task.actual_session.id
    task.delete()
    
    return JsonResponse({'success': True, 'message': 'Task deleted successfully'})


@facilitator_required
def facilitator_task_complete(request, actual_session_id):
    """
    Mark facilitator task step as complete and move to attendance marking
    """
    actual_session = get_object_or_404(ActualSession, id=actual_session_id)
    
    # Check if at least one task exists
    task_count = FacilitatorTask.objects.filter(
        actual_session=actual_session,
        facilitator=request.user
    ).count()
    
    if task_count == 0:
        messages.warning(request, "Please add at least one task before proceeding")
        return redirect('facilitator_task_step', actual_session_id=actual_session_id)
    
    # Update session status to mark attendance
    actual_session.status = 'conducted'
    actual_session.save()
    
    messages.success(request, "Facilitator task completed. Now mark attendance.")
    # Redirect to mark_attendance instead of start_session to avoid loop
    return redirect('mark_attendance', actual_session_id=actual_session_id)
