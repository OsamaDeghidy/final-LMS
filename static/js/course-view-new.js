/**
 * Course View Page JavaScript
 * Handles all interactive functionality for the course view page
 * Includes progress tracking for videos, quizzes, PDFs, and assignments
 */

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

    // Content item click handlers
    const contentItems = document.querySelectorAll('.content-item');
    contentItems.forEach(item => {
        item.addEventListener('click', function(e) {
            // Don't prevent default as we want the links to work
            const contentType = this.getAttribute('data-content-type');
            const contentId = this.getAttribute('data-content-id');
            
            if (contentType && contentId) {
                // Mark the item as accessed in the UI
                markItemAsAccessed(contentType, contentId);
            }
        });
    });

    // Quiz completion handling
    const quizCompleteButtons = document.querySelectorAll('.quiz-complete-btn');
    quizCompleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            const quizId = this.getAttribute('data-quiz-id');
            const score = this.getAttribute('data-score');
            
            if (!quizId || !score) {
                console.error('Missing quiz ID or score for quiz completion');
                return;
            }
            
            // Send completion data to server
            markQuizCompleted(quizId, score);
        });
    });
});

// Function to mark video as watched
function markVideoAsWatched(videoElement) {
    const videoId = videoElement.getAttribute('data-video-id');
    if (!videoId) {
        console.error('Video element does not have data-video-id attribute');
        return;
    }
    
    // Send AJAX request to mark video as watched
    fetch(`/mark_video_watched/${videoId}/`, {
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
            const sidebarItem = document.querySelector(`[data-content-type="video"][data-content-id="${videoId}"]`);
            if (sidebarItem) {
                sidebarItem.classList.add('completed');
                const icon = sidebarItem.querySelector('.content-icon i');
                if (icon) {
                    icon.classList.remove('fa-play');
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
    fetch(`/mark_quiz_completed/${quizId}/`, {
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
            const quizItem = document.querySelector(`[data-content-type="quiz"][data-content-id="${quizId}"]`);
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

// Helper to show next content
function showNextContent() {
    const nextContentBtn = document.getElementById('next-content-btn');
    if (nextContentBtn) {
        const nextContentType = nextContentBtn.getAttribute('data-next-type');
        const nextContentId = nextContentBtn.getAttribute('data-next-id');
        const courseId = document.querySelector('meta[name="course-id"]')?.content;
        
        if (nextContentType && nextContentId && courseId) {
            // Build the URL with query parameters for the next content
            window.location.href = `/courseviewpage/${courseId}/?content_type=${nextContentType}&content_id=${nextContentId}`;
        } else {
            // Fallback to simple reload
            window.location.reload();
        }
    } else {
        // No next button, just reload
        window.location.reload();
    }
}

// Function to get CSRF token
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

// Function to update progress bar
function updateProgressBar(progress) {
    const progressBar = document.querySelector('.progress-bar');
    const progressText = document.querySelector('.progress-text');
    
    if (progressBar) {
        progressBar.style.width = `${progress}%`;
        progressBar.setAttribute('aria-valuenow', progress);
    }
    
    if (progressText) {
        progressText.textContent = `إكمال الدورة: ${Math.round(progress)}%`;
    }
    
    // Also update the stats grid if it exists
    updateStatsGrid();
}

// Function to update the stats grid
function updateStatsGrid() {
    // This would need to be implemented if we want to update the count displays
    // without a page reload. For now, the next content navigation will refresh the page.
}

// Function to mark item as accessed in UI
function markItemAsAccessed(contentType, contentId) {
    // Find the content item in the sidebar
    const selector = `[data-content-type="${contentType}"][data-content-id="${contentId}"]`;
    const contentItem = document.querySelector(selector);
    
    if (contentItem) {
        // Add a visual indicator that it has been accessed
        contentItem.classList.add('accessed');
        
        // Add a small dot or icon to indicate it's been accessed
        if (!contentItem.querySelector('.accessed-indicator')) {
            const indicator = document.createElement('span');
            indicator.className = 'accessed-indicator';
            indicator.innerHTML = '<i class="fas fa-eye"></i>';
            contentItem.appendChild(indicator);
        }
    }
}
