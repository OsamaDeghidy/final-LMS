from django import template

register = template.Library()

@register.filter
def filter_by_user(attempts, user):
    """
    Filter exam attempts by user
    Usage: {{ attempts|filter_by_user:request.user }}
    """
    return attempts.filter(user=user)

@register.filter
def get_user_attempts_count(exam, user):
    """
    Get the count of attempts by a user for an exam
    Usage: {{ exam|get_user_attempts_count:request.user }}
    """
    return exam.attempts.filter(user=user).count()

@register.filter
def get_latest_attempt(exam, user):
    """
    Get the latest attempt by a user for an exam
    Usage: {{ exam|get_latest_attempt:request.user }}
    """
    attempts = exam.attempts.filter(user=user).order_by('-start_time')
    return attempts.first() if attempts.exists() else None

@register.filter
def format_duration(seconds):
    """
    Format seconds into a readable duration (HH:MM:SS)
    Usage: {{ seconds|format_duration }}
    """
    if not seconds:
        return "00:00:00"
    
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

@register.filter
def can_retake_exam(exam, user):
    """
    Check if a user can retake an exam
    Usage: {{ exam|can_retake_exam:request.user }}
    """
    if not exam.allow_multiple_attempts:
        return False
    
    attempts_count = exam.attempts.filter(user=user).count()
    return attempts_count < exam.max_attempts
