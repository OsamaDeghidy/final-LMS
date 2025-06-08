"""
Utility functions for the website application.
All course-related utilities have been moved to utils_course.py
"""

# Import all course-related utility functions from utils_course
from .utils_course import *

# Import models that might be used in other utility functions
from .models import ContentProgress, Enrollment
from django.utils import timezone

# Import user models if needed
from user.models import Student  # noqa: F401