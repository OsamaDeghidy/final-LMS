// Course Content Enhanced JavaScript

document.addEventListener('DOMContentLoaded', function() {
    
    // تهيئة الشريط الجانبي
    initSidebar();
    
    // تحديث شريط التقدم
    updateProgressBar();
    
    // إعداد navigation
    setupNavigation();
    
    // إعداد video controls
    setupVideoControls();
    
    // إعداد quiz functionality
    setupQuizzes();
});

// تهيئة الشريط الجانبي
function initSidebar() {
    // فتح الوحدة الحالية تلقائياً
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
            const moduleId = firstModule.id;
            const toggleIcon = document.getElementById('icon-' + moduleId);
            if (toggleIcon) {
                toggleIcon.classList.add('rotated');
            }
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
    // إعداد أزرار التنقل
    const navButtons = document.querySelectorAll('.nav-btn');
    navButtons.forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            // إضافة loading effect
            const icon = this.querySelector('i');
            if (icon) {
                const originalClass = icon.className;
                icon.className = 'fas fa-spinner fa-spin';
                
                setTimeout(() => {
                    icon.className = originalClass;
                }, 1000);
            }
        });
    });
    
    // إعداد زر إعادة حساب التقدم
    const recalculateBtn = document.querySelector('.recalculate-progress-btn');
    if (recalculateBtn) {
        recalculateBtn.addEventListener('click', function() {
            const courseId = this.dataset.courseId;
            recalculateProgress(courseId);
        });
    }
    
    // إعداد زر إنهاء الدورة
    const completeCourseBtn = document.querySelector('.complete-course-btn');
    if (completeCourseBtn) {
        completeCourseBtn.addEventListener('click', function() {
            const courseId = this.dataset.courseId;
            completeCourse(courseId);
        });
    }
}

// إعداد video controls
function setupVideoControls() {
    const videos = document.querySelectorAll('.video-player');
    
    videos.forEach(function(video) {
        const videoId = video.dataset.videoId;
        const courseId = video.dataset.courseId;
        
        if (videoId && courseId) {
            // تتبع وقت المشاهدة
            let watchedTime = 0;
            let totalTime = 0;
            let marked = false;
            
            video.addEventListener('loadedmetadata', function() {
                totalTime = video.duration;
            });
            
            video.addEventListener('timeupdate', function() {
                watchedTime = video.currentTime;
                const progress = (watchedTime / totalTime) * 100;
                
                // تحديث progress bar إذا وجد
                const progressBar = document.getElementById('video-progress-' + videoId);
                if (progressBar) {
                    progressBar.style.width = progress + '%';
                    const progressText = progressBar.querySelector('.progress-text');
                    if (progressText) {
                        progressText.textContent = Math.round(progress) + '%';
                    }
                }
                
                // mark as viewed when 80% watched
                if (progress >= 80 && !marked) {
                    markContentViewed('video', videoId);
                    marked = true;
                }
            });
            
            // حفظ التقدم عند المغادرة
            window.addEventListener('beforeunload', function() {
                if (watchedTime > 0) {
                    // يمكن إضافة حفظ التقدم هنا
                }
            });
        }
    });
}

// إعداد quiz functionality
function setupQuizzes() {
    // إعداد أزرار بدء الاختبار
    const startQuizBtns = document.querySelectorAll('.start-quiz-btn');
    startQuizBtns.forEach(function(btn) {
        btn.addEventListener('click', function() {
            const quizId = this.dataset.quizId;
            startQuiz(quizId);
        });
    });
    
    // إعداد نماذج الاختبار
    const quizForms = document.querySelectorAll('[id^="quiz-form-"]');
    quizForms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            submitQuiz(form);
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
        
        // بدء العد التنازلي
        startQuizTimer(quizId);
        
        // scroll to quiz
        questionsContainer.scrollIntoView({ behavior: 'smooth' });
    }
}

// العد التنازلي للاختبار
function startQuizTimer(quizId) {
    const timerElement = document.getElementById('quiz-timer-' + quizId);
    if (!timerElement) return;
    
    const timeText = timerElement.textContent;
    const timeMatch = timeText.match(/(\d+):(\d+)/);
    if (!timeMatch) return;
    
    let minutes = parseInt(timeMatch[1]);
    let seconds = parseInt(timeMatch[2]);
    let totalSeconds = (minutes * 60) + seconds;
    
    const timer = setInterval(function() {
        totalSeconds--;
        
        if (totalSeconds <= 0) {
            clearInterval(timer);
            // تسليم تلقائي
            const form = document.getElementById('quiz-form-' + quizId);
            if (form) {
                alert('انتهى الوقت! سيتم تسليم الاختبار تلقائياً.');
                submitQuiz(form);
            }
            return;
        }
        
        const mins = Math.floor(totalSeconds / 60);
        const secs = totalSeconds % 60;
        timerElement.textContent = mins + ':' + (secs < 10 ? '0' : '') + secs;
        
        // تغيير اللون عند اقتراب الوقت
        if (totalSeconds <= 300) { // 5 minutes
            timerElement.style.color = 'red';
        } else if (totalSeconds <= 600) { // 10 minutes
            timerElement.style.color = 'orange';
        }
    }, 1000);
}

// تسليم الاختبار
function submitQuiz(form) {
    const formData = new FormData(form);
    const submitBtn = form.querySelector('button[type="submit"]');
    
    // إظهار loading
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>جاري التسليم...';
    }
    
    fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': formData.get('csrfmiddlewaretoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showQuizResults(data);
            // إعادة تحميل الصفحة لتحديث التقدم
            setTimeout(() => {
                location.reload();
            }, 3000);
        } else {
            alert('حدث خطأ: ' + (data.message || 'خطأ غير معروف'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('حدث خطأ أثناء تسليم الاختبار');
    })
    .finally(() => {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-paper-plane me-1"></i>تسليم الإجابات';
        }
    });
}

// عرض نتائج الاختبار
function showQuizResults(data) {
    const resultHtml = `
        <div class="quiz-results alert alert-${data.passed ? 'success' : 'warning'}">
            <h5><i class="fas fa-${data.passed ? 'check-circle' : 'exclamation-triangle'} me-2"></i>
                نتيجة الاختبار
            </h5>
            <p><strong>النتيجة:</strong> ${data.score}% (${data.correct_answers}/${data.total_questions})</p>
            <p><strong>الحالة:</strong> ${data.passed ? 'نجحت في الاختبار!' : 'لم تحقق الدرجة المطلوبة'}</p>
            ${data.passed ? '<p class="mb-0 text-success">تهانينا! يمكنك المتابعة للدرس التالي.</p>' : 
                          '<p class="mb-0 text-warning">يمكنك إعادة المحاولة لاحقاً.</p>'}
        </div>
    `;
    
    // البحث عن مكان إدراج النتائج
    const quizContainer = document.querySelector('.quiz-display-container');
    if (quizContainer) {
        quizContainer.insertAdjacentHTML('beforeend', resultHtml);
        
        // scroll to results
        const resultsElement = quizContainer.querySelector('.quiz-results');
        if (resultsElement) {
            resultsElement.scrollIntoView({ behavior: 'smooth' });
        }
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
            // تحديث UI
            const contentItem = document.querySelector(`[data-content-id="${contentId}"]`);
            if (contentItem) {
                contentItem.classList.add('completed');
                const icon = contentItem.querySelector('.content-icon i');
                if (icon) {
                    icon.className = 'fas fa-check';
                }
            }
            
            // تحديث progress bar
            updateProgressBar();
        }
    })
    .catch(error => {
        console.error('Error marking content as viewed:', error);
    });
}

// إعادة حساب التقدم
function recalculateProgress(courseId) {
    const btn = document.querySelector('.recalculate-progress-btn');
    if (btn) {
        const originalIcon = btn.querySelector('i').className;
        btn.querySelector('i').className = 'fas fa-spinner fa-spin';
        btn.disabled = true;
    }
    
    fetch(`/recalculate-progress/${courseId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert('حدث خطأ أثناء إعادة حساب التقدم');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('حدث خطأ أثناء إعادة حساب التقدم');
    })
    .finally(() => {
        if (btn) {
            btn.querySelector('i').className = originalIcon;
            btn.disabled = false;
        }
    });
}

// إنهاء الدورة
function completeCourse(courseId) {
    if (!confirm('هل أنت متأكد من أنك تريد إنهاء هذه الدورة؟')) {
        return;
    }
    
    const btn = document.querySelector('.complete-course-btn');
    if (btn) {
        const originalContent = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>جاري الإنهاء...';
        btn.disabled = true;
    }
    
    fetch(`/complete-course/${courseId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('تهانينا! لقد أنهيت الدورة بنجاح. ' + (data.certificate_url ? 'يمكنك تحميل الشهادة الآن.' : ''));
            location.reload();
        } else {
            alert('حدث خطأ: ' + (data.message || 'لا يمكن إنهاء الدورة'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('حدث خطأ أثناء إنهاء الدورة');
    })
    .finally(() => {
        if (btn) {
            btn.innerHTML = originalContent;
            btn.disabled = false;
        }
    });
}

// تحسين تجربة المستخدم
document.addEventListener('DOMContentLoaded', function() {
    // إضافة smooth scrolling للروابط
    const links = document.querySelectorAll('a[href*="#"]');
    links.forEach(function(link) {
        link.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href.startsWith('#')) {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            }
        });
    });
    
    // إضافة keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Space = play/pause video
        if (e.code === 'Space' && !['INPUT', 'TEXTAREA'].includes(e.target.tagName)) {
            const video = document.querySelector('.video-player');
            if (video) {
                e.preventDefault();
                if (video.paused) {
                    video.play();
                } else {
                    video.pause();
                }
            }
        }
        
        // Arrow keys for navigation
        if (e.code === 'ArrowLeft' && e.ctrlKey) {
            const nextBtn = document.querySelector('.nav-btn.next');
            if (nextBtn) {
                nextBtn.click();
            }
        } else if (e.code === 'ArrowRight' && e.ctrlKey) {
            const prevBtn = document.querySelector('.nav-btn.prev');
            if (prevBtn) {
                prevBtn.click();
            }
        }
    });
});

// Global function to make toggleModule available
window.toggleModule = toggleModule; 