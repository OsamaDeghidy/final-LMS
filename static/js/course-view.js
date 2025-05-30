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

    // Comment form submission
    const commentForms = document.querySelectorAll('.comment-form');
    commentForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            // Add AJAX functionality here for submitting comments
            
            // Example feedback:
            const textarea = this.querySelector('textarea');
            if (textarea.value.trim() !== '') {
                // Clear textarea after submission
                textarea.value = '';
                
                // Show success message (you can enhance this)
                const successAlert = document.createElement('div');
                successAlert.className = 'alert alert-success mt-3';
                successAlert.textContent = 'تم إرسال تعليقك بنجاح وسيظهر بعد المراجعة';
                this.appendChild(successAlert);
                
                // Remove alert after 3 seconds
                setTimeout(() => {
                    successAlert.remove();
                }, 3000);
            }
        });
    });

    // Reply button functionality
    const replyButtons = document.querySelectorAll('.reply-button');
    replyButtons.forEach(button => {
        button.addEventListener('click', function() {
            const commentId = this.dataset.commentId;
            const replyForm = document.getElementById(`reply-form-${commentId}`);
            
            // Toggle form visibility
            if (replyForm) {
                if (replyForm.classList.contains('d-none')) {
                    replyForm.classList.remove('d-none');
                    button.innerHTML = '<i class="fas fa-times me-1"></i> إلغاء';
                } else {
                    replyForm.classList.add('d-none');
                    button.innerHTML = '<i class="fas fa-reply me-1"></i> رد';
                }
            }
        });
    });

    // Helpful/like button functionality
    const likeButtons = document.querySelectorAll('.like-button');
    likeButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Get current likes count
            let likesText = this.textContent.match(/\((\d+)\)/);
            let likesCount = likesText ? parseInt(likesText[1]) : 0;
            
            // Toggle liked state
            if (this.classList.contains('text-primary')) {
                // Unlike
                this.classList.remove('text-primary');
                this.classList.add('text-muted');
                likesCount = Math.max(0, likesCount - 1);
            } else {
                // Like
                this.classList.remove('text-muted');
                this.classList.add('text-primary');
                likesCount += 1;
            }
            
            // Update text
            this.innerHTML = `<i class="far fa-thumbs-up me-1"></i> مفيد (${likesCount})`;
        });
    });

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Progress tracking (this would typically be handled by backend)
    // This is just a visual example
    const progressBars = document.querySelectorAll('.progress-bar');
    progressBars.forEach(bar => {
        const targetWidth = bar.style.width;
        bar.style.width = '0%';
        
        setTimeout(() => {
            bar.style.width = targetWidth;
        }, 500);
    });
    
    // Track quiz progress
    const quizLinks = document.querySelectorAll('.quiz-item');
    quizLinks.forEach(link => {
        link.addEventListener('click', function() {
            const quizId = this.getAttribute('data-quiz-id');
            // Record that user accessed this quiz
            recordContentAccess('quiz', quizId);
        });
    });
    
    // Track assignment progress
    const assignmentLinks = document.querySelectorAll('.assignment-item');
    assignmentLinks.forEach(link => {
        link.addEventListener('click', function() {
            const assignmentId = this.getAttribute('data-assignment-id');
            // Record that user accessed this assignment
            recordContentAccess('assignment', assignmentId);
        });
    });
    
    // Track PDF progress
    const pdfLinks = document.querySelectorAll('.pdf-item');
    pdfLinks.forEach(link => {
        link.addEventListener('click', function() {
            const pdfId = this.getAttribute('data-pdf-id');
            // Record that user accessed this PDF
            recordContentAccess('pdf', pdfId);
        });
    });
    
    // Video progress tracking
    const videos = document.querySelectorAll('video');
    videos.forEach(video => {
        // Resume video from last position
        video.addEventListener('loadedmetadata', function() {
            const lastPosition = this.getAttribute('data-last-position');
            if (lastPosition) {
                this.currentTime = parseInt(lastPosition);
            }
        });

        // Track progress
        let progressInterval;
        video.addEventListener('play', function() {
            progressInterval = setInterval(() => {
                const progress = (this.currentTime / this.duration) * 100;
                if (progress > 90 && !this.hasAttribute('data-watched')) {
                    markVideoAsWatched(this);
                }
            }, 5000);
        });

        video.addEventListener('pause', function() {
            clearInterval(progressInterval);
            saveVideoProgress(this);
        });

        video.addEventListener('ended', function() {
            clearInterval(progressInterval);
            markVideoAsWatched(this);
        });
    });
    
    // Content switching functionality
    const contentItems = document.querySelectorAll('.content-item');
    const contentSections = document.querySelectorAll('.content-section');

    contentItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('data-content-id');
            
            // Update active states
            contentItems.forEach(i => i.classList.remove('active'));
            this.classList.add('active');
            
            // Show target content
            contentSections.forEach(section => {
                if (section.id === targetId) {
                    section.classList.remove('d-none');
                } else {
                    section.classList.add('d-none');
                }
            });
        });
    });

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
}); // End of DOMContentLoaded

// Function to mark video as watched
function markVideoAsWatched(videoElement) {
    const videoId = videoElement.closest('.content-section').id.replace('video-', '');
    
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
            // Add completion badge
            const container = videoElement.closest('.video-container');
            if (!container.querySelector('.video-completed-badge')) {
                const badge = document.createElement('div');
                badge.className = 'video-completed-badge';
                badge.innerHTML = '<i class="fas fa-check-circle"></i> تم مشاهدة هذا الفيديو';
                container.appendChild(badge);
            }
            
            // Update sidebar icon
            const sidebarItem = document.querySelector(`[data-content-id="video-${videoId}"] .icon-wrapper`);
            if (sidebarItem) {
                sidebarItem.classList.remove('bg-primary');
                sidebarItem.classList.add('bg-success');
                sidebarItem.querySelector('.fas').classList.replace('fa-play', 'fa-check');
            }
            
            // Update progress bar
            const progressBar = document.querySelector('.progress-bar');
            if (progressBar && data.progress) {
                progressBar.style.width = `${data.progress}%`;
                progressBar.setAttribute('aria-valuenow', data.progress);
                document.querySelector('.progress span').textContent = `${Math.floor(data.progress)}%`;
            }
        }
    });
}

// Function to save video progress
function saveVideoProgress(videoElement) {
    const videoId = videoElement.closest('.content-section').id.replace('video-', '');
    const currentTime = Math.floor(videoElement.currentTime);
    
    fetch(`/api/video/${videoId}/save-progress/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            current_time: currentTime
        })
    });
}

// Helpful/like button functionality
const likeButtons = document.querySelectorAll('.like-button');
likeButtons.forEach(button => {
    button.addEventListener('click', function() {
        // Get current likes count
        let likesText = this.textContent.match(/\((\d+)\)/);
        let likesCount = likesText ? parseInt(likesText[1]) : 0;
        
        // Toggle liked state
        if (this.classList.contains('text-primary')) {
            // Unlike
            this.classList.remove('text-primary');
            this.classList.add('text-muted');
            likesCount = Math.max(0, likesCount - 1);
        } else {
            // Like
            this.classList.remove('text-muted');
            this.classList.add('text-primary');
            likesCount += 1;
        }
        
        // Update text
        this.innerHTML = `<i class="far fa-thumbs-up me-1"></i> مفيد (${likesCount})`;
    });
});

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        
        const targetId = this.getAttribute('href');
        if (targetId === '#') return;
        
        const targetElement = document.querySelector(targetId);
        if (targetElement) {
            targetElement.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Progress tracking (this would typically be handled by backend)
// This is just a visual example
const progressBars = document.querySelectorAll('.progress-bar');
progressBars.forEach(bar => {
    const targetWidth = bar.style.width;
    bar.style.width = '0%';
    
    setTimeout(() => {
        bar.style.width = targetWidth;
    }, 500);
});
    
// Track quiz progress
const quizLinks = document.querySelectorAll('.quiz-item');
quizLinks.forEach(link => {
    link.addEventListener('click', function() {
        const quizId = this.getAttribute('data-quiz-id');
        // Record that user accessed this quiz
        recordContentAccess('quiz', quizId);
    });
});
    
// Track assignment progress
const assignmentLinks = document.querySelectorAll('.assignment-item');
assignmentLinks.forEach(link => {
    link.addEventListener('click', function() {
        const assignmentId = this.getAttribute('data-assignment-id');
        // Record that user accessed this assignment
        recordContentAccess('assignment', assignmentId);
    });
});
    
// Track PDF progress
const pdfLinks = document.querySelectorAll('.pdf-item');
pdfLinks.forEach(link => {
    link.addEventListener('click', function() {
        const pdfId = this.getAttribute('data-pdf-id');
        // Record that user accessed this PDF
        recordContentAccess('pdf', pdfId);
    });
});

// Function to mark video as watched
function markVideoAsWatched(videoElement) {
    const videoId = videoElement.closest('.content-section').id.replace('video-', '');
    
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
            // Add completion badge
            const container = videoElement.closest('.video-container');
            if (!container.querySelector('.video-completed-badge')) {
                const badge = document.createElement('div');
                badge.className = 'video-completed-badge';
                badge.innerHTML = '<i class="fas fa-check-circle"></i> تم مشاهدة هذا الفيديو';
                container.appendChild(badge);
            }
            
            // Update sidebar icon
            const sidebarItem = document.querySelector(`[data-content-id="video-${videoId}"] .icon-wrapper`);
            if (sidebarItem) {
                sidebarItem.classList.remove('bg-primary');
                sidebarItem.classList.add('bg-success');
                sidebarItem.querySelector('.fas').classList.replace('fa-play', 'fa-check');
            }
            
            // Update progress bar
            const progressBar = document.querySelector('.progress-bar');
            if (progressBar && data.progress) {
                progressBar.style.width = `${data.progress}%`;
                progressBar.setAttribute('aria-valuenow', data.progress);
                document.querySelector('.progress span').textContent = `${Math.floor(data.progress)}%`;
            }
        }
    });
}

// Function to save video progress
function saveVideoProgress(videoElement) {
    const videoId = videoElement.closest('.content-section').id.replace('video-', '');
    const currentTime = Math.floor(videoElement.currentTime);
    
    fetch(`/api/video/${videoId}/save-progress/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            current_time: currentTime
        })
    });
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

// Function to record access to different content types (quiz, assignment, pdf)
function recordContentAccess(contentType, contentId) {
    fetch(`/api/content-access/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            content_type: contentType,
            content_id: contentId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Update progress bar if progress data is returned
            if (data.progress) {
                updateProgressBar(data.progress);
            }
            
            // Mark item as accessed in UI
            markItemAsAccessed(contentType, contentId);
        }
    })
    .catch(error => {
        console.error('Error recording content access:', error);
    });
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
        progressText.textContent = `${Math.floor(progress)}%`;
    }
}

// Function to mark item as accessed in UI
function markItemAsAccessed(contentType, contentId) {
    const item = document.querySelector(`[data-${contentType}-id="${contentId}"]`);
    
    if (item) {
        // Add visual indicator that item was accessed
        if (!item.querySelector('.content-accessed')) {
            const accessedBadge = document.createElement('small');
            accessedBadge.className = 'content-accessed text-success ms-2';
            accessedBadge.innerHTML = '<i class="fas fa-eye"></i>';
            
            const titleElement = item.querySelector('.content-title');
            if (titleElement) {
                titleElement.appendChild(accessedBadge);
            }
        }
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // Content switching functionality
    const contentItems = document.querySelectorAll('.content-item');
    const contentSections = document.querySelectorAll('.content-section');

    contentItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('data-content-id');
            
            // Update active states
            contentItems.forEach(i => i.classList.remove('active'));
            this.classList.add('active');
            
            // Show target content
            contentSections.forEach(section => {
                if (section.id === targetId) {
                    section.classList.remove('d-none');
                } else {
                    section.classList.add('d-none');
                }
            });
        });
    });

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
        // Resume video from last position
        video.addEventListener('loadedmetadata', function() {
            const lastPosition = this.getAttribute('data-last-position');
            if (lastPosition) {
                this.currentTime = parseInt(lastPosition);
            }
        });

        // Track progress
        let progressInterval;
        video.addEventListener('play', function() {
            progressInterval = setInterval(() => {
                const progress = (this.currentTime / this.duration) * 100;
                if (progress > 90 && !this.hasAttribute('data-watched')) {
                    markVideoAsWatched(this);
                }
            }, 5000);
        });

        video.addEventListener('pause', function() {
            clearInterval(progressInterval);
            saveVideoProgress(this);
        });

        video.addEventListener('ended', function() {
            clearInterval(progressInterval);
            markVideoAsWatched(this);
        });
    });
});

// Handle video progress tracking
document.addEventListener('DOMContentLoaded', function() {
    // Handle video position saving
    const videos = document.querySelectorAll('video');
    videos.forEach(video => {
      const videoId = video.closest('.content-section').id.replace('video-', '');
      
      // Load saved position if exists
      if(video.dataset.lastPosition) {
        video.currentTime = parseFloat(video.dataset.lastPosition);
      }
      
      // Save position periodically
      video.addEventListener('timeupdate', function() {
        localStorage.setItem(`video_${videoId}_position`, video.currentTime);
      });
      
      // Mark as completed when video ends
      video.addEventListener('ended', function() {
        // Here you would typically send an AJAX request to mark as completed
        console.log(`Video ${videoId} completed`);
        video.dataset.watched = "true";
        
        // Update UI
        const badge = document.createElement('div');
        badge.className = 'video-completed-badge position-absolute top-0 end-0 m-3';
        badge.innerHTML = `<span class="badge bg-success rounded-pill px-3 py-2 shadow-sm">
          <i class="fas fa-check-circle me-1"></i> تم المشاهدة
        </span>`;
        video.parentElement.appendChild(badge);
      });
    });
    
    // Handle content switching
    const contentItems = document.querySelectorAll('.content-item');
    contentItems.forEach(item => {
      item.addEventListener('click', function(e) {
        e.preventDefault();
        const contentId = this.dataset.contentId;
        
        // Hide all content sections
        document.querySelectorAll('.content-section').forEach(section => {
          section.classList.add('d-none');
        });
        
        // Show selected content
        document.getElementById(contentId).classList.remove('d-none');
        
        // Update active state
        contentItems.forEach(i => i.classList.remove('active', 'bg-light-primary'));
        this.classList.add('active', 'bg-light-primary');
      });
    });
    
    // Handle quiz submission
    const quizForm = document.getElementById('ques');
    if(quizForm) {
      quizForm.addEventListener('submit', function(e) {
        e.preventDefault();
        // Here you would typically send an AJAX request
        console.log('Quiz submitted');
        
        // Show results
        document.getElementById('results').classList.remove('d-none');
        quizForm.classList.add('d-none');
      });
    }
  });

