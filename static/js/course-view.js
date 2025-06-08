
document.addEventListener('DOMContentLoaded', function() {
    // تعيين عرض شريط التقدم
    const progressBar = document.querySelector('.progress-fill');
    
    // فتح وغلق أقسام المحتوى
    window.toggleModule = function(moduleId) {
        const moduleContent = document.getElementById(moduleId);
        const icon = document.getElementById('icon-' + moduleId);
        
        if (moduleContent.style.display === 'none' || moduleContent.style.display === '') {
            moduleContent.style.display = 'block';
            icon.classList.remove('fa-chevron-down');
            icon.classList.add('fa-chevron-up');
        } else {
            moduleContent.style.display = 'none';
            icon.classList.remove('fa-chevron-up');
            icon.classList.add('fa-chevron-down');
        }
    }
    const sidebarProgressBar = document.querySelector('.progress-fill-sidebar');
    
    if (progressBar) {
        const progress = progressBar.dataset.progress || 0;
        progressBar.style.width = progress + '%';
        
        // Set dynamic progress attributes
        document.querySelector('.progress-section').setAttribute('data-progress', progress);
        document.querySelector('.sidebar-header').setAttribute('data-progress', progress);
    }
    
    if (sidebarProgressBar) {
        const progress = sidebarProgressBar.dataset.progress || 0;
        sidebarProgressBar.style.width = progress + '%';
    }
    
    // إظهار الوحدة الأولى بشكل افتراضي
    const firstModule = document.querySelector('.module-content');
    if (firstModule) {
        firstModule.classList.add('active');
        const firstIcon = document.querySelector('.toggle-icon');
        if (firstIcon) {
            firstIcon.classList.remove('fa-chevron-down');
            firstIcon.classList.add('fa-chevron-up');
        }
    }
    
    // إظهار الوحدة التي تحتوي على المحتوى الحالي
    const activeContent = document.querySelector('.content-item.active');
    if (activeContent) {
        const activeModule = activeContent.closest('.module-content');
        if (activeModule) {
            activeModule.classList.add('active');
            const moduleId = activeModule.id;
            const icon = document.getElementById('icon-' + moduleId);
            if (icon) {
                icon.classList.remove('fa-chevron-down');
                icon.classList.add('fa-chevron-up');
            }
        }
        
        // Add current class to active content
        activeContent.classList.add('current');
    }
    
    // إضافة event listeners لجميع عناصر المحتوى
    const contentItems = document.querySelectorAll('.content-item[data-content-type]');
    contentItems.forEach(item => {
        item.addEventListener('click', function(e) {
            // Update current position indicator
            updateCurrentPosition(this);
            
            const contentType = this.dataset.contentType;
            const contentId = this.dataset.contentId;
            if (contentType && contentId) {
                // تأجيل تسجيل التقدم قليلاً حتى يتم تحميل الصفحة
                setTimeout(() => {
                    markContentViewed(contentType, contentId);
                }, 1000);
            }
        });
    });
    
    // Update completion counter on page load
    updateCompletionCounter();
    
    // Recalculate Progress Button Handler
    const recalculateBtn = document.querySelector('.recalculate-progress-btn');
    if (recalculateBtn) {
        recalculateBtn.addEventListener('click', function() {
            const courseId = this.dataset.courseId;
            recalculateProgress(courseId);
        });
    }
    
    // Course Completion Button Handler
    const completeCourseBtn = document.querySelector('.complete-course-btn');
    if (completeCourseBtn) {
        completeCourseBtn.addEventListener('click', function() {
            const courseId = this.dataset.courseId;
            if (confirm('هل أنت متأكد من إنهاء هذه الدورة؟ سيتم وضع علامة مكتملة نهائياً.')) {
                completeCourse(courseId);
            }
        });
    }
    
    // Add high progress class for styling
    const progressValue = parseFloat('{{ progress|default:0 }}');
    if (progressValue >= 80) {
        document.body.classList.add('high-progress');
        
        // Add appropriate progress section classes
        const progressSection = document.querySelector('.progress-section');
        if (progressSection) {
            if (progressValue >= 100) {
                progressSection.classList.add('completed');
            } else if (progressValue >= 90) {
                progressSection.classList.add('near-completion');
            }
        }
    }
    
    // تتبع التقدم الديناميكي
    const video = document.querySelector('.course-video');
    if (video) {
        let hasMarked = false;
        
        video.addEventListener('ended', function() {
            if (!hasMarked) {
                markVideoCompleted(this.dataset.videoId);
                hasMarked = true;
            }
        });
        
        // تتبع الوقت المشاهد
        video.addEventListener('timeupdate', function() {
            const percent = (video.currentTime / video.duration) * 100;
            if (percent > 90 && !hasMarked) { // إذا شاهد 90% من الفيديو
                markVideoCompleted(this.dataset.videoId);
                hasMarked = true;
            }
        });
        
        // Mark video as viewed after 3 seconds
        setTimeout(() => {
            if (!hasMarked) {
                markContentViewed('video', video.dataset.videoId);
            }
        }, 3000);
    }
    
    // تتبع عرض PDFs والملاحظات
    const noteContainer = document.querySelector('.note-display-container');
    if (noteContainer) {
        setTimeout(() => {
            const noteId = noteContainer.dataset.noteId || new URLSearchParams(window.location.search).get('content_id');
            if (noteId) {
                markContentViewed('note', noteId);
            }
        }, 2000); // بعد ثانيتين من فتح المحتوى
    }
    
    // وظائف الكويز
    const startQuizBtns = document.querySelectorAll('.start-quiz-btn');
    startQuizBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const quizId = this.dataset.quizId;
            startQuiz(quizId);
        });
    });
    
    // تسجيل التقدم التلقائي للمحتوى الحالي
    const currentContentType = new URLSearchParams(window.location.search).get('content_type');
    const currentContentId = new URLSearchParams(window.location.search).get('content_id');
    
    if (currentContentType && currentContentId) {
        // تسجيل أن المستخدم فتح هذا المحتوى
        console.log('Auto-tracking content:', currentContentType, currentContentId);
        setTimeout(() => {
            markContentViewed(currentContentType, currentContentId);
        }, 3000); // بعد 3 ثوان من فتح المحتوى
    } else {
        // If no specific content, this is the overview page
        console.log('On course overview page');
    }
});

// وظيفة تحديث المؤشر الحالي
function updateCurrentPosition(clickedItem) {
    // Remove current class from all items
    document.querySelectorAll('.content-item').forEach(item => {
        item.classList.remove('current');
    });
    
    // Add current class to clicked item
    clickedItem.classList.add('current');
    
    // Update position indicator if it exists
    const positionIndicator = document.querySelector('.current-position-indicator');
    if (positionIndicator) {
        const contentType = clickedItem.dataset.contentType;
        const contentName = clickedItem.querySelector('.content-name').textContent;
        const contentIcon = clickedItem.querySelector('.content-icon i').className;
        
        const currentContentInfo = positionIndicator.querySelector('.current-content-info');
        if (currentContentInfo) {
            currentContentInfo.innerHTML = `<i class="${contentIcon} me-1"></i>${contentName}`;
        }
    }
}

// وظيفة تحديث عداد الإكمال
function updateCompletionCounter() {
    const completedCount = document.querySelectorAll('.content-item.completed').length;
    const completedCountElement = document.getElementById('completed-count');
    
    if (completedCountElement) {
        completedCountElement.textContent = completedCount;
        
        // Add animation when count updates
        completedCountElement.style.transform = 'scale(1.2)';
        setTimeout(() => {
            completedCountElement.style.transform = 'scale(1)';
        }, 200);
    }
}

function toggleModule(moduleId) {
    const content = document.getElementById(moduleId);
    const icon = document.getElementById('icon-' + moduleId);
    
    if (!content || !icon) return;
    
    content.classList.toggle('active');
    
    if (content.classList.contains('active')) {
        icon.classList.remove('fa-chevron-down');
        icon.classList.add('fa-chevron-up');
    } else {
        icon.classList.remove('fa-chevron-up');
        icon.classList.add('fa-chevron-down');
    }
}

function markProgress(contentType, contentId) {
    // التحقق من وجود CSRF token
    const csrfToken = getCookie('csrftoken');
    if (!csrfToken) {
        console.error('CSRF token not found');
        return;
    }
    
    // إرسال طلب لتسجيل التقدم
    fetch(`/api/${contentType}/${contentId}/mark-completed/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            content_type: contentType,
            content_id: contentId
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success' || data.success) {
            if (data.progress !== undefined) {
                updateProgressBar(data.progress);
            }
            markContentAsCompleted(contentType, contentId);
        } else {
            console.log('Progress tracking response:', data.message || 'No progress update');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function markVideoCompleted(videoId) {
    const csrfToken = getCookie('csrftoken');
    if (!csrfToken) {
        console.error('CSRF token not found');
        return;
    }
    
    fetch(`/api/video/${videoId}/mark-watched/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            video_id: videoId
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success' || data.success) {
            // تحديث واجهة المستخدم
            if (data.progress !== undefined) {
                updateProgressBar(data.progress);
            }
            markContentAsCompleted('video', videoId);
            
            // إظهار رسالة نجاح
            console.log('Video marked as completed successfully');
        } else {
            console.log('Video completion response:', data.message || 'No progress update');
        }
    })
    .catch(error => {
        console.error('Error marking video as completed:', error);
    });
}

function updateProgressBar(progress) {
    if (typeof progress === 'undefined' || progress === null) return;
    
    console.log('Updating progress to:', progress + '%');
    
    // تحديث شريط التقدم الرئيسي
    const progressBar = document.querySelector('.progress-fill');
    if (progressBar) {
        progressBar.style.width = Math.min(100, Math.max(0, progress)) + '%';
        progressBar.setAttribute('data-progress', progress);
        
        // Update dynamic progress attributes
        const progressSection = document.querySelector('.progress-section');
        if (progressSection) {
            progressSection.setAttribute('data-progress', progress);
            
            // Add completion classes based on progress
            progressSection.classList.remove('completed', 'near-completion');
            if (progress >= 100) {
                progressSection.classList.add('completed');
            } else if (progress >= 90) {
                progressSection.classList.add('near-completion');
            }
        }
    }
    
    // تحديث شريط التقدم في الـ Sidebar
    const sidebarProgressBar = document.querySelector('.progress-fill-sidebar');
    if (sidebarProgressBar) {
        sidebarProgressBar.style.width = Math.min(100, Math.max(0, progress)) + '%';
        sidebarProgressBar.setAttribute('data-progress', progress);
        
        // Update sidebar header dynamic attributes
        const sidebarHeader = document.querySelector('.sidebar-header');
        if (sidebarHeader) {
            sidebarHeader.setAttribute('data-progress', progress);
        }
    }
    
    // تحديث النص
    const progressTitle = document.querySelector('.progress-title');
    if (progressTitle) {
        progressTitle.innerHTML = `<i class="fas fa-chart-line me-2"></i>تقدمك في الدورة: ${progress.toFixed(1)}%`;
    }
    
    // تحديث نص الـ Sidebar
    const sidebarProgressTitle = document.querySelector('.progress-title-sidebar');
    if (sidebarProgressTitle) {
        sidebarProgressTitle.innerHTML = `<i class="fas fa-chart-line me-2"></i>تقدمك: ${progress.toFixed(1)}%`;
    }
    
    // Update completion counter
    updateCompletionCounter();
    
    // إظهار رسالة تقدم إذا تم إحراز تقدم
    const currentProgress = parseFloat('{{ progress|default:0 }}');
    if (progress > currentProgress) {
        showMessage(`تم تحديث التقدم: ${progress.toFixed(1)}%`, 'success');
        
        // Update page progress value for completion button logic
        if (progress >= 90) {
            // Show completion button if progress is high enough
            setTimeout(() => {
                location.reload(); // Reload to show completion button
            }, 2000);
        }
    }
    
    // Add celebration effect if progress reaches milestones
    if (progress >= 100) {
        addCelebrationEffect('🎉 تهانينا! أكملت الدورة بنجاح!');
    } else if (progress >= 90) {
        addCelebrationEffect('🎊 ممتاز! أوشكت على إنهاء الدورة!');
    } else if (progress >= 75) {
        addCelebrationEffect('👍 رائع! أكملت ثلاثة أرباع الدورة!');
    } else if (progress >= 50) {
        addCelebrationEffect('💪 ممتاز! وصلت لنصف الدورة!');
    } else if (progress >= 25) {
        addCelebrationEffect('🚀 بداية رائعة! استمر!');
    }
}

// وظيفة إضافة تأثير الاحتفال
function addCelebrationEffect(message) {
    // Prevent showing the same message repeatedly
    if (window.lastCelebrationProgress === Math.floor(parseFloat('{{ progress|default:0 }}'))) {
        return;
    }
    
    const celebration = document.createElement('div');
    celebration.className = 'celebration-popup';
    celebration.innerHTML = `
        <div class="celebration-content">
            <div class="celebration-icon">🎉</div>
            <div class="celebration-message">${message}</div>
        </div>
    `;
    
    // Add CSS for the celebration popup
    celebration.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        z-index: 1000;
        animation: celebrationBounce 0.6s ease;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        text-align: center;
        min-width: 300px;
    `;
    
    document.body.appendChild(celebration);
    
    setTimeout(() => {
        celebration.remove();
    }, 3000);
    
    window.lastCelebrationProgress = Math.floor(parseFloat('{{ progress|default:0 }}'));
}

// Add CSS animation for celebration
const celebrationStyle = document.createElement('style');
celebrationStyle.textContent = `
    @keyframes celebrationBounce {
        0% { transform: translate(-50%, -50%) scale(0.3) rotate(-15deg); opacity: 0; }
        50% { transform: translate(-50%, -50%) scale(1.1) rotate(5deg); opacity: 1; }
        100% { transform: translate(-50%, -50%) scale(1) rotate(0deg); opacity: 1; }
    }
    
    .celebration-content {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 1rem;
    }
    
    .celebration-icon {
        font-size: 3rem;
        animation: bounce 1s infinite;
    }
    
    .celebration-message {
        font-size: 1.2rem;
        font-weight: 600;
        text-align: center;
    }
`;
document.head.appendChild(celebrationStyle);

function markContentAsCompleted(type, id) {
    const contentItem = document.querySelector(`[data-content-type="${type}"][data-content-id="${id}"]`);
    if (contentItem && !contentItem.classList.contains('completed')) {
        contentItem.classList.add('completed');
        const icon = contentItem.querySelector('.content-icon i');
        if (icon) {
            icon.className = 'fas fa-check';
        }
        
        // إضافة شارة الإكمال
        if (!contentItem.querySelector('.completion-badge')) {
            const badge = document.createElement('div');
            badge.className = 'completion-badge';
            badge.innerHTML = '<i class="fas fa-check"></i>';
            contentItem.appendChild(badge);
        }
        
        // Update completion counter
        updateCompletionCounter();
        
        // Trigger progress recalculation
        setTimeout(() => {
            calculateAndUpdateProgress();
        }, 500);
        
        // Add completion animation
        contentItem.style.animation = 'completionPulse 0.6s ease';
        setTimeout(() => {
            contentItem.style.animation = '';
        }, 600);
    }
}

// Add completion animation CSS
const completionAnimationStyle = document.createElement('style');
completionAnimationStyle.textContent = `
    @keyframes completionPulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4); }
        100% { transform: scale(1); }
    }
`;
document.head.appendChild(completionAnimationStyle);

function getCookie(name) {
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

function markContentViewed(contentType, contentId) {
    const csrfToken = getCookie('csrftoken');
    if (!csrfToken) return;
    
    fetch(`/api/${contentType}/${contentId}/mark-viewed/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            content_type: contentType,
            content_id: contentId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success' || data.success) {
            console.log('Content marked as viewed successfully');
            if (data.progress !== undefined) {
                updateProgressBar(data.progress);
            }
            // Mark content as completed in UI
            markContentAsCompleted(contentType, contentId);
        }
    })
    .catch(error => {
        console.error('Error marking content as viewed:', error);
    });
}

function startQuiz(quizId) {
    const quizQuestions = document.getElementById(`quiz-questions-${quizId}`);
    const startBtn = document.querySelector(`[data-quiz-id="${quizId}"]`);
    
    if (quizQuestions && startBtn) {
        // إخفاء زر البدء وإظهار الأسئلة
        startBtn.style.display = 'none';
        quizQuestions.style.display = 'block';
        
        // بدء العد التنازلي
        startQuizTimer(quizId);
        
        // تمرير الصفحة إلى الأسئلة
        quizQuestions.scrollIntoView({ behavior: 'smooth' });
    }
}

function startQuizTimer(quizId) {
    // الحصول على مدة الكويز (افتراضي 15 دقيقة)
    const timeLimit = 15 * 60; // بالثواني
    let timeLeft = timeLimit;
    
    // إنشاء عنصر العداد
    const timerDiv = document.createElement('div');
    timerDiv.className = 'quiz-timer active';
    timerDiv.id = `quiz-timer-${quizId}`;
    document.body.appendChild(timerDiv);
    
    const timer = setInterval(() => {
        const minutes = Math.floor(timeLeft / 60);
        const seconds = timeLeft % 60;
        
        timerDiv.innerHTML = `
            <i class="fas fa-clock me-2"></i>
            الوقت المتبقي: ${minutes}:${seconds.toString().padStart(2, '0')}
        `;
        
        // تحذير عندما يبقى 5 دقائق
        if (timeLeft <= 5 * 60) {
            timerDiv.classList.add('warning');
        }
        
        // انتهاء الوقت
        if (timeLeft <= 0) {
            clearInterval(timer);
            timerDiv.remove();
            submitQuizAutomatically(quizId);
        }
        
        timeLeft--;
    }, 1000);
}

function submitQuizAutomatically(quizId) {
    const form = document.getElementById(`quiz-form-${quizId}`);
    if (form) {
        // إضافة رسالة تنبيه
        const alert = document.createElement('div');
        alert.className = 'alert alert-warning';
        alert.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>انتهى الوقت! تم تسليم الاختبار تلقائياً.';
        form.insertBefore(alert, form.firstChild);
        
        // تسليم النموذج
        setTimeout(() => {
            form.submit();
        }, 2000);
    }
}

// إضافة معالج للأخطاء العامة
window.addEventListener('error', function(e) {
    console.error('JavaScript error:', e.error);
});

// إضافة دالة مساعدة لإظهار الرسائل
function showMessage(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} position-fixed`;
    alertDiv.style.cssText = `
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 1050;
        min-width: 300px;
        text-align: center;
    `;
    alertDiv.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'warning' ? 'exclamation-triangle' : 'info-circle'} me-2"></i>
        ${message}
    `;
    
    document.body.appendChild(alertDiv);
    
    // إزالة الرسالة بعد 3 ثوان
    setTimeout(() => {
        alertDiv.remove();
    }, 3000);
}

// تتبع التقدم الديناميكي
function updateProgress() {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    fetch('{% url "dashboard" %}', {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => response.text())
    .then(data => {
        // Parse the response to get updated progress
        const parser = new DOMParser();
        const doc = parser.parseFromString(data, 'text/html');
        
        // Try to get progress from the response (this is a simple approach)
        // Better approach would be a dedicated API endpoint
        calculateAndUpdateProgress();
    })
    .catch(error => {
        console.error('Error updating progress:', error);
        calculateAndUpdateProgress();
    });
}

function calculateAndUpdateProgress() {
    // Use data from the page instead of template loops
    const totalItems = parseInt('{{ total_videos|default:0 }}') + parseInt('{{ total_notes|default:0 }}') + parseInt('{{ total_quizzes|default:0 }}');
    
    if (totalItems === 0) {
        updateProgressBars(0);
        return;
    }
    
    // Get completed items from page data
    const completedVideos = document.querySelectorAll('.content-item.completed[data-content-type="video"]').length;
    const completedPdfs = document.querySelectorAll('.content-item.completed[data-content-type="note"]').length;
    const completedQuizzes = document.querySelectorAll('.content-item.completed[data-content-type="quiz"]').length;
    
    const completedItems = completedVideos + completedPdfs + completedQuizzes;
    const progressPercentage = Math.round((completedItems / totalItems) * 100);
    
    console.log('Progress calculation:', {
        totalItems,
        completedVideos,
        completedPdfs, 
        completedQuizzes,
        completedItems,
        progressPercentage
    });
    
    updateProgressBars(progressPercentage);
}

function updateProgressBars(percentage) {
    // Update main progress bar
    const mainProgressBar = document.querySelector('.progress-bar');
    const mainProgressText = document.querySelector('.progress-text');
    
    if (mainProgressBar) {
        mainProgressBar.style.width = percentage + '%';
        mainProgressBar.setAttribute('aria-valuenow', percentage);
        if (mainProgressText) {
            mainProgressText.textContent = percentage + '%';
        }
    }
    
    // Update sidebar progress bar
    const sidebarProgressBar = document.querySelector('.sidebar-progress .progress-bar');
    const sidebarProgressText = document.querySelector('.sidebar-progress .progress-text');
    
    if (sidebarProgressBar) {
        sidebarProgressBar.style.width = percentage + '%';
        sidebarProgressBar.setAttribute('aria-valuenow', percentage);
        if (sidebarProgressText) {
            sidebarProgressText.textContent = percentage + '%';
        }
    }
    
    // Update course overview progress if visible
    const overviewProgress = document.querySelector('.course-progress-bar .progress-bar');
    if (overviewProgress) {
        overviewProgress.style.width = percentage + '%';
        overviewProgress.setAttribute('aria-valuenow', percentage);
    }
    
    // Update progress text in overview
    const overviewProgressText = document.querySelector('.progress-percentage');
    if (overviewProgressText) {
        overviewProgressText.textContent = percentage + '%';
    }
}

function markContentAsViewed(contentType, contentId) {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    fetch(`/mark-content-viewed/${contentType}/${contentId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            console.log('Content marked as viewed successfully');
            if (data.progress !== undefined) {
                updateProgressBars(data.progress);
            } else {
                // Recalculate progress locally
                setTimeout(() => {
                    calculateAndUpdateProgress();
                }, 500);
            }
        } else {
            console.error('Error marking content as viewed:', data.message);
        }
    })
    .catch(error => {
        console.error('Error marking content as viewed:', error);
    });
}

// تتبع مشاهدة الفيديو
function setupVideoTracking() {
    const video = document.querySelector('video');
    if (video) {
        let hasTrackedView = false;
        let progressInterval;
        
        video.addEventListener('loadedmetadata', function() {
            console.log('Video loaded, duration:', video.duration);
        });
        
        video.addEventListener('timeupdate', function() {
            const progress = (video.currentTime / video.duration) * 100;
            
            // Mark as viewed when user watches 90% or more than 30 seconds
            if (!hasTrackedView && (progress >= 90 || video.currentTime >= 30)) {
                hasTrackedView = true;
                const videoId = video.getAttribute('data-video-id');
                if (videoId) {
                    markContentAsViewed('video', videoId);
                }
            }
        });
        
        video.addEventListener('ended', function() {
            if (!hasTrackedView) {
                hasTrackedView = true;
                const videoId = video.getAttribute('data-video-id');
                if (videoId) {
                    markContentAsViewed('video', videoId);
                }
            }
        });
    }
}

// تتبع عرض الملاحظات
function setupNoteTracking() {
    const noteContainer = document.querySelector('.note-display-container');
    if (noteContainer) {
        let hasTrackedView = false;
        let viewTimer;
        
        // Mark as viewed after 3 seconds of viewing
        viewTimer = setTimeout(() => {
            if (!hasTrackedView) {
                hasTrackedView = true;
                const noteId = noteContainer.getAttribute('data-note-id') || 
                             new URLSearchParams(window.location.search).get('content_id');
                if (noteId) {
                    markContentAsViewed('note', noteId);
                }
            }
        }, 3000);
        
        // Clear timer if user leaves the page
        window.addEventListener('beforeunload', () => {
            if (viewTimer) {
                clearTimeout(viewTimer);
            }
        });
    }
}

// تتبع الاختبارات
function setupQuizTracking() {
    const quizForm = document.querySelector('.quiz-form');
    if (quizForm) {
        quizForm.addEventListener('submit', function(e) {
            // Quiz completion will be handled by the server
            // Progress will be updated when the form is submitted
        });
    }
}

// Initialize progress tracking
document.addEventListener('DOMContentLoaded', function() {
    // Initial progress calculation
    calculateAndUpdateProgress();
    
    // Setup content tracking
    setupVideoTracking();
    setupNoteTracking();
    setupQuizTracking();
    setupPDFMarkingButtons();
    setupAssignmentMarkingButtons();
    
    // Update progress every 30 seconds
    setInterval(calculateAndUpdateProgress, 30000);
});

// Course Completion Function
function completeCourse(courseId) {
    const csrfToken = getCookie('csrftoken');
    if (!csrfToken) {
        showMessage('خطأ في الأمان - يرجى إعادة تحميل الصفحة', 'error');
        return;
    }
    
    // Show loading
    const completeBtn = document.querySelector('.complete-course-btn');
    if (completeBtn) {
        completeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري الإنهاء...';
        completeBtn.disabled = true;
    }
    
    fetch(`/api/course/${courseId}/complete/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            course_id: courseId,
            force_complete: true
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success' || data.success) {
            // Update progress to 100%
            updateProgressBar(100);
            
            // Update button to completed state
            if (completeBtn) {
                completeBtn.innerHTML = '<i class="fas fa-check-circle"></i> مكتملة بنجاح';
                completeBtn.className = 'nav-btn nav-btn-success completed-btn';
                completeBtn.disabled = true;
            }
            
            // Add celebration animation
            document.body.classList.add('completed-course');
            
            // Show success message
            showMessage('🎉 تهانينا! تم إنهاء الدورة بنجاح', 'success');
            
            // Show final exam if available
            const finalExamBtn = document.querySelector('.final-exam-btn');
            if (finalExamBtn) {
                finalExamBtn.style.display = 'inline-flex';
                finalExamBtn.classList.add('final-exam-available');
            }
            
            // Reload page after 2 seconds to show updated state
            setTimeout(() => {
                window.location.reload();
            }, 2000);
            
        } else {
            throw new Error(data.message || 'فشل في إنهاء الدورة');
        }
    })
    .catch(error => {
        console.error('Error completing course:', error);
        showMessage('حدث خطأ أثناء إنهاء الدورة: ' + error.message, 'error');
        
        // Reset button
        if (completeBtn) {
            completeBtn.innerHTML = '<i class="fas fa-trophy"></i> إنهاء الدورة';
            completeBtn.disabled = false;
        }
    });
}

// Recalculate Progress Function
function recalculateProgress(courseId) {
    const csrfToken = getCookie('csrftoken');
    if (!csrfToken) {
        showMessage('خطأ في الأمان - يرجى إعادة تحميل الصفحة', 'error');
        return;
    }
    
    // Show loading
    const recalculateBtn = document.querySelector('.recalculate-progress-btn');
    if (recalculateBtn) {
        recalculateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        recalculateBtn.disabled = true;
    }
    
    fetch(`/api/course/${courseId}/recalculate-progress/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            // Update progress bars
            updateProgressBar(data.progress);
            
            showMessage(`تم إعادة حساب التقدم: ${data.progress.toFixed(1)}%`, 'success');
            
            // Reload page to show updated completion status
            setTimeout(() => {
                window.location.reload();
            }, 1500);
            
        } else {
            throw new Error(data.message || 'فشل في إعادة حساب التقدم');
        }
    })
    .catch(error => {
        console.error('Error recalculating progress:', error);
        showMessage('حدث خطأ أثناء إعادة حساب التقدم: ' + error.message, 'error');
    })
    .finally(() => {
        // Reset button
        if (recalculateBtn) {
            recalculateBtn.innerHTML = '<i class="fas fa-sync-alt"></i>';
            recalculateBtn.disabled = false;
        }
    });
}

// تحديد ملف PDF كمقروء
function setupPDFMarkingButtons() {
    document.querySelectorAll('.mark-pdf-read-btn').forEach(button => {
        button.addEventListener('click', function() {
            const pdfId = this.dataset.pdfId || this.dataset.noteId;
            const courseId = this.dataset.courseId;
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            
            // تغيير حالة الزر
            this.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>جاري التحديث...';
            this.disabled = true;
            
            fetch('{% url "courses:mark_pdf_read" %}', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrfToken
                },
                body: `pdf_id=${pdfId}&course_id=${courseId}`
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // تحديث الزر
                    this.innerHTML = '<i class="fas fa-check-circle me-2"></i>تم التحديد كمقروء';
                    this.classList.remove('btn-info');
                    this.classList.add('btn-success');
                    
                    // تحديث شريط التقدم
                    updateProgress();
                    
                    // تحديث القائمة الجانبية
                    const sidebarItem = document.querySelector(`[data-content-id="${pdfId}"]`);
                    if (sidebarItem) {
                        sidebarItem.classList.add('completed');
                        const icon = sidebarItem.querySelector('.content-icon i');
                        if (icon) {
                            icon.className = 'fas fa-check';
                        }
                        
                        // إضافة شارة الإكمال
                        if (!sidebarItem.querySelector('.completion-badge')) {
                            const badge = document.createElement('div');
                            badge.className = 'completion-badge';
                            badge.innerHTML = '<i class="fas fa-check"></i>';
                            sidebarItem.appendChild(badge);
                        }
                    }
                    
                    // عرض رسالة نجاح
                    showMessage('تم تحديد الملف كمقروء بنجاح', 'success');
                } else {
                    // إعادة الزر لحالته الأصلية
                    this.innerHTML = '<i class="fas fa-check-circle me-2"></i>تحديد كمقروء';
                    this.disabled = false;
                    
                    // عرض رسالة خطأ
                    showMessage('حدث خطأ أثناء تحديث حالة الملف', 'danger');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                this.innerHTML = '<i class="fas fa-check-circle me-2"></i>تحديد كمقروء';
                this.disabled = false;
                showMessage('حدث خطأ أثناء الاتصال بالخادم', 'danger');
            });
        });
    });
}

// تحديد الواجب كمكتمل
function setupAssignmentMarkingButtons() {
    document.querySelectorAll('.mark-assignment-completed-btn').forEach(button => {
        button.addEventListener('click', function() {
            const assignmentId = this.dataset.assignmentId;
            const courseId = this.dataset.courseId;
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            
            // تغيير حالة الزر
            this.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>جاري التحديث...';
            this.disabled = true;
            
            fetch('{% url "mark_assignment_completed" 0 %}'.replace('0', assignmentId), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrfToken
                },
                body: `assignment_id=${assignmentId}&course_id=${courseId}`
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // تحديث الزر
                    this.innerHTML = '<i class="fas fa-check-circle me-2"></i>مكتمل';
                    this.classList.remove('btn-primary');
                    this.classList.add('btn-success');
                    
                    // تحديث شريط التقدم
                    updateProgress();
                    
                    // تحديث القائمة الجانبية
                    const sidebarItem = document.querySelector(`[data-content-id="${assignmentId}"][data-content-type="assignment"]`);
                    if (sidebarItem) {
                        sidebarItem.classList.add('completed');
                        const icon = sidebarItem.querySelector('.content-icon i');
                        if (icon) {
                            icon.className = 'fas fa-check';
                        }
                        
                        // إضافة شارة الإكمال
                        if (!sidebarItem.querySelector('.completion-badge')) {
                            const badge = document.createElement('div');
                            badge.className = 'completion-badge';
                            badge.innerHTML = '<i class="fas fa-check"></i>';
                            sidebarItem.appendChild(badge);
                        }
                    }
                    
                    // عرض رسالة نجاح
                    showMessage('تم تحديد الواجب كمكتمل بنجاح', 'success');
                } else {
                    // إعادة الزر لحالته الأصلية
                    this.innerHTML = '<i class="fas fa-check me-2"></i>تحديد كمكتمل';
                    this.disabled = false;
                    
                    // عرض رسالة خطأ
                    showMessage('حدث خطأ أثناء تحديث حالة الواجب', 'danger');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                this.innerHTML = '<i class="fas fa-check me-2"></i>تحديد كمكتمل';
                this.disabled = false;
                showMessage('حدث خطأ أثناء الاتصال بالخادم', 'danger');
            });
        });
    });
}
