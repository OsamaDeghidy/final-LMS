/**
 * Course View Page JavaScript
 * Handles all interactive functionality for the course view page
 * Includes progress tracking for videos, quizzes, PDFs, and assignments
 */

// Function to get CSRF token from cookies
function getCsrfToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Function to update progress bar in the UI
function updateProgressBar(progress) {
    const progressBar = document.querySelector('.course-progress-bar .progress-bar');
    const progressText = document.querySelector('.course-progress-percentage');
    
    if (progressBar) {
        // Update progress bar width
        progressBar.style.width = `${progress}%`;
        progressBar.setAttribute('aria-valuenow', progress);
    }
    
    if (progressText) {
        // Update progress text
        progressText.textContent = `${Math.round(progress)}%`;
    }
}

// Function to mark video as watched
function markVideoAsWatched(videoElement) {
    const videoId = videoElement.getAttribute('data-video-id');
    if (!videoId) {
        console.error('Video element does not have data-video-id attribute');
        return;
    }
    
    // Send AJAX request to mark video as watched
    fetch(`/api/video/${videoId}/mark-watched/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Update UI
            const badge = document.createElement('div');
            badge.className = 'video-completed-badge position-absolute top-0 end-0 m-3';
            badge.innerHTML = '<span class="badge bg-success rounded-pill px-3 py-2 shadow-sm"><i class="fas fa-check-circle me-1"></i> تم المشاهدة</span>';
            videoElement.parentElement.appendChild(badge);
            
            // Update progress bar
            if (data.progress) {
                updateProgressBar(data.progress);
            }
            
            // Update the sidebar item
            const sidebarItem = document.querySelector(`.content-item[data-content-type="video"][data-content-id="${videoId}"]`);
            if (sidebarItem) {
                sidebarItem.classList.add('completed');
                const icon = sidebarItem.querySelector('.content-icon i');
                if (icon) {
                    icon.classList.remove('fa-play-circle');
                    icon.classList.add('fa-check-circle');
                }
                
                // Add completed badge if it doesn't exist
                if (!sidebarItem.querySelector('.completed-badge')) {
                    const badge = document.createElement('div');
                    badge.className = 'completed-badge';
                    badge.innerHTML = '<i class="fas fa-check"></i>';
                    sidebarItem.appendChild(badge);
                }
            }
        }
    })
    .catch(error => console.error('Error marking video as watched:', error));
}

// Function to mark quiz as completed
function markQuizCompleted(quizId, score) {
    fetch(`/api/quiz/${quizId}/mark-completed/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ score: score })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Update UI to show completion
            const quizItem = document.querySelector(`.content-item[data-content-type="quiz"][data-content-id="${quizId}"]`);
            if (quizItem) {
                quizItem.classList.add('completed');
                const icon = quizItem.querySelector('.content-icon i');
                if (icon) {
                    icon.classList.remove('fa-question-circle');
                    icon.classList.add('fa-check-circle');
                }
                
                // Add completed badge if it doesn't exist
                if (!quizItem.querySelector('.completed-badge')) {
                    const badge = document.createElement('div');
                    badge.className = 'completed-badge';
                    badge.innerHTML = '<i class="fas fa-check"></i>';
                    quizItem.appendChild(badge);
                }
            }
            
            // Update progress bar
            if (data.progress) {
                updateProgressBar(data.progress);
            }
            
            // Show success message
            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert alert-success mt-3';
            alertDiv.textContent = 'تم إكمال الاختبار بنجاح!';
            document.querySelector('#dynamic-content-area').appendChild(alertDiv);
            
            // Remove alert after 3 seconds
            setTimeout(() => {
                alertDiv.remove();
                // Show next content if available
                showNextContent();
            }, 3000);
        }
    })
    .catch(error => {
        console.error('Error marking quiz as completed:', error);
        // Show error message
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger mt-3';
        alertDiv.textContent = 'حدث خطأ أثناء تسجيل إكمال الاختبار. يرجى المحاولة مرة أخرى.';
        document.querySelector('#dynamic-content-area').appendChild(alertDiv);
        
        // Remove alert after 3 seconds
        setTimeout(() => {
            alertDiv.remove();
        }, 3000);
    });
}

// Function to save video progress
function saveVideoProgress(videoElement) {
    const videoId = videoElement.getAttribute('data-video-id');
    if (!videoId) {
        console.error('Video element does not have data-video-id attribute');
        return;
    }
    
    // Save to localStorage
    localStorage.setItem(`video-progress-${videoId}`, videoElement.currentTime.toString());
}

// Function to show next content item
function showNextContent() {
    // Find the current active content item in the sidebar
    const currentItem = document.querySelector('.content-item.active');
    if (!currentItem) return;
    
    // Find the next content item
    let nextItem = currentItem.nextElementSibling;
    while (nextItem && !nextItem.classList.contains('content-item')) {
        nextItem = nextItem.nextElementSibling;
    }
    
    // If there's a next item, navigate to it
    if (nextItem) {
        window.location.href = nextItem.href;
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Module collapse indicators
    const moduleHeaders = document.querySelectorAll('.module-header');
    moduleHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const icon = this.querySelector('.fas');
            const isExpanded = this.getAttribute('aria-expanded') === 'true';
            
            if (isExpanded) {
                icon.classList.remove('fa-chevron-up');
                icon.classList.add('fa-chevron-down');
            } else {
                icon.classList.remove('fa-chevron-down');
                icon.classList.add('fa-chevron-up');
            }
        });
    });

    // Video progress tracking
    const videos = document.querySelectorAll('video');
    videos.forEach(video => {
        // Get video ID from data attribute
        const videoId = video.getAttribute('data-video-id');
        if (!videoId) return;
        
        // Load saved progress from localStorage
        const savedProgress = localStorage.getItem(`video-progress-${videoId}`);
        if (savedProgress) {
            video.currentTime = parseFloat(savedProgress);
        }
        
        // Save progress periodically
        setInterval(() => {
            if (!video.paused && video.currentTime > 0) {
                saveVideoProgress(video);
            }
        }, 5000);

        // Mark video as watched when 90% complete
        video.addEventListener('timeupdate', function() {
            if (video.currentTime >= video.duration * 0.9 && !video.hasBeenMarkedComplete) {
                video.hasBeenMarkedComplete = true; // Prevent multiple calls
                markVideoAsWatched(video);
            }
        });
    });

    // Next button handler
    const nextBtn = document.getElementById('next-content-btn');
    if (nextBtn) {
        nextBtn.addEventListener('click', function() {
            showNextContent();
        });
    }

    // Quiz submit button handler
    const quizSubmitBtns = document.querySelectorAll('.quiz-submit-btn');
    quizSubmitBtns.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const quizId = this.getAttribute('data-quiz-id');
            if (!quizId) {
                console.error('Quiz submit button does not have data-quiz-id attribute');
                return;
            }
            
            // Calculate score based on selected answers
            const quizForm = document.getElementById(`quiz-form-${quizId}`);
            if (!quizForm) {
                console.error('Quiz form not found');
                return;
            }
            
            // Get all questions and calculate score
            const questions = quizForm.querySelectorAll('.quiz-question');
            let correctAnswers = 0;
            let totalQuestions = questions.length;
            
            questions.forEach(question => {
                const selectedAnswer = question.querySelector('input[type="radio"]:checked');
                if (selectedAnswer && selectedAnswer.getAttribute('data-correct') === 'true') {
                    correctAnswers++;
                }
            });
            
            // Calculate percentage score
            const score = totalQuestions > 0 ? (correctAnswers / totalQuestions) * 100 : 0;
            
            // Mark quiz as completed
            markQuizCompleted(quizId, score);
        });
    });

    // Content item click handlers for tracking
    const contentItems = document.querySelectorAll('.content-item');
    contentItems.forEach(item => {
        item.addEventListener('click', function() {
            const contentType = this.getAttribute('data-content-type');
            const contentId = this.getAttribute('data-content-id');
            
            // We don't prevent default here as we want the link to work
            // Just log that the content was accessed
            console.log(`Content accessed: ${contentType} ${contentId}`);
        });
    });
});
