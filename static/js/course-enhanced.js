// Course Content Enhanced JavaScript

document.addEventListener('DOMContentLoaded', function() {
    initSidebar();
    updateProgressBar();
    setupNavigation();
    setupVideoControls();
    setupQuizzes();
});

// تهيئة الشريط الجانبي
function initSidebar() {
    const currentModuleContent = document.querySelector('.module-content:has(.content-item.active)');
    if (currentModuleContent) {
        currentModuleContent.classList.add('show');
        const moduleId = currentModuleContent.id;
        const toggleIcon = document.getElementById('icon-' + moduleId);
        if (toggleIcon) {
            toggleIcon.classList.add('rotated');
        }
    }
    
    // فتح أول وحدة إذا لم يكن هناك محتوى نشط
    if (!currentModuleContent) {
        const firstModule = document.querySelector('.module-content');
        if (firstModule) {
            firstModule.classList.add('show');
        }
    }
}

// وظيفة تبديل الوحدات
function toggleModule(moduleId) {
    const moduleContent = document.getElementById(moduleId);
    const toggleIcon = document.getElementById('icon-' + moduleId);
    
    if (moduleContent && toggleIcon) {
        const isShown = moduleContent.classList.contains('show');
        
        if (isShown) {
            moduleContent.classList.remove('show');
            toggleIcon.classList.remove('rotated');
        } else {
            moduleContent.classList.add('show');
            toggleIcon.classList.add('rotated');
        }
    }
}

// تحديث شريط التقدم
function updateProgressBar() {
    const progressBars = document.querySelectorAll('.progress-fill, .progress-fill-sidebar');
    
    progressBars.forEach(function(bar) {
        const progress = parseFloat(bar.dataset.progress) || 0;
        bar.style.width = Math.min(progress, 100) + '%';
    });
}

// إعداد navigation
function setupNavigation() {
    const recalculateBtn = document.querySelector('.recalculate-progress-btn');
    if (recalculateBtn) {
        recalculateBtn.addEventListener('click', function() {
            const courseId = this.dataset.courseId;
            recalculateProgress(courseId);
        });
    }
}

// إعداد video controls
function setupVideoControls() {
    const videos = document.querySelectorAll('.video-player');
    
    videos.forEach(function(video) {
        const videoId = video.dataset.videoId;
        
        if (videoId) {
            let marked = false;
            
            video.addEventListener('timeupdate', function() {
                const progress = (video.currentTime / video.duration) * 100;
                
                if (progress >= 80 && !marked) {
                    markContentViewed('video', videoId);
                    marked = true;
                }
            });
        }
    });
}

// إعداد quiz functionality
function setupQuizzes() {
    const startQuizBtns = document.querySelectorAll('.start-quiz-btn');
    startQuizBtns.forEach(function(btn) {
        btn.addEventListener('click', function() {
            const quizId = this.dataset.quizId;
            startQuiz(quizId);
        });
    });
}

// بدء الاختبار
function startQuiz(quizId) {
    const questionsContainer = document.getElementById('quiz-questions-' + quizId);
    const startPanel = questionsContainer?.previousElementSibling;
    
    if (questionsContainer && startPanel) {
        startPanel.style.display = 'none';
        questionsContainer.style.display = 'block';
    }
}

// تحديد المحتوى كمشاهد
function markContentViewed(contentType, contentId) {
    fetch(`/mark-content-viewed/${contentType}/${contentId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const contentItem = document.querySelector(`[data-content-id="${contentId}"]`);
            if (contentItem) {
                contentItem.classList.add('completed');
            }
            updateProgressBar();
        }
    })
    .catch(error => {
        console.error('Error marking content as viewed:', error);
    });
}

// إعادة حساب التقدم
function recalculateProgress(courseId) {
    fetch(`/recalculate-progress/${courseId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// Global function
window.toggleModule = toggleModule; 