/**
 * Enhanced Progress System for Course Modules
 * نظام التقدم المحسن للموديولات
 * 
 * كل موديول يحتوي على 5 عناصر: فيديو، PDF، ملاحظات، واجب، اختبار
 * إذا كان هناك موديولين، فكل موديول يستحق 50%
 * كل عنصر من الـ5 عناصر يستحق 10% من نسبة الموديول
 */

class EnhancedProgressSystem {
    constructor() {
        this.elementsPerModule = 5; // فيديو، PDF، ملاحظات، واجب، اختبار
        this.modules = [];
        this.totalProgress = 0;
        
        console.log('🎯 Enhanced Progress System initialized');
        this.init();
    }
    
    async init() {
        // تحميل الموديولات
        this.loadModules();
        
        // تحميل الإكمال المحفوظ
        this.loadStoredCompletions();
        
        // حساب التقدم الأولي
        await this.calculateOverallProgress();
        
        // إعداد مراقبة التغييرات
        this.setupProgressTracking();
        
        // تحديث دوري
        this.setupPeriodicUpdate();
    }
    
    loadModules() {
        const moduleElements = document.querySelectorAll('.module-item');
        this.modules = Array.from(moduleElements).map((element, index) => {
            const moduleContent = element.querySelector('.module-content');
            const moduleId = moduleContent ? moduleContent.id.replace('module-', '') : 'module-' + index;
            const moduleName = element.querySelector('.module-title')?.textContent.trim() || `Module ${index + 1}`;
            
            return {
                id: moduleId,
                name: moduleName,
                element: element,
                progressPercentage: 100 / moduleElements.length, // نسبة كل موديول من إجمالي الدورة
                elements: this.getModuleElements(element)
            };
        });
        
        console.log(`📚 Loaded ${this.modules.length} modules:`, this.modules.map(m => m.name));
    }
    
    getModuleElements(moduleElement) {
        const moduleContent = moduleElement.querySelector('.module-content');
        if (!moduleContent) return {};
        
        return {
            video: moduleContent.querySelector('.content-item[data-content-type="video"], .content-item[data-content-type="module_video"]'),
            pdf: moduleContent.querySelector('.content-item[data-content-type="pdf"], .content-item[data-content-type="module_pdf"]'),
            note: moduleContent.querySelector('.content-item[data-content-type="note"], .content-item[data-content-type="module_note"]'),
            assignment: moduleContent.querySelector('.content-item[data-content-type="assignment"]'),
            quiz: moduleContent.querySelector('.content-item[data-content-type="quiz"]')
        };
    }
    
    calculateModuleProgress(module) {
        let completedElements = 0;
        let totalElements = 0;
        
        // حساب العناصر المكتملة
        Object.keys(module.elements).forEach(elementType => {
            const element = module.elements[elementType];
            if (element) {
                totalElements++;
                if (element.classList.contains('completed')) {
                    completedElements++;
                }
            }
        });
        
        // حساب نسبة الإكمال للموديول
        const moduleCompletionRate = totalElements > 0 ? (completedElements / totalElements) : 0;
        const moduleProgress = moduleCompletionRate * module.progressPercentage;
        
        console.log(`📊 Module "${module.name}": ${completedElements}/${totalElements} elements (${(moduleCompletionRate * 100).toFixed(1)}%) = ${moduleProgress.toFixed(1)}% of total`);
        
        return {
            completed: completedElements,
            total: totalElements,
            completionRate: moduleCompletionRate,
            progressPoints: moduleProgress
        };
    }
    
    async calculateOverallProgress() {
        let totalProgressPoints = 0;
        let moduleProgressData = [];
        
        this.modules.forEach(module => {
            const progress = this.calculateModuleProgress(module);
            totalProgressPoints += progress.progressPoints;
            
            moduleProgressData.push({
                module: module,
                progress: progress
            });
            
            // تحديث عرض تقدم الموديول
            this.updateModuleDisplay(module, progress);
        });
        
        this.totalProgress = Math.min(totalProgressPoints, 100);
        
        console.log(`🎯 Overall Progress: ${this.totalProgress.toFixed(1)}%`);
        console.log('📈 Module breakdown:', moduleProgressData);

        // التحقق من الامتحان النهائي أولاً قبل تحديث العرض
        const finalExamPassed = await this.checkFinalExamFromDatabase();
        
        if (finalExamPassed) {
            // إذا نجح في الامتحان النهائي، النسبة 100%
            this.totalProgress = 100.0;
            console.log('🎓 Final exam passed - Course completed at 100%');
            this.updateProgressDisplay(); // استخدام دالة العرض المحسنة
            this.markCourseAsCompleted(); // تسجيل الكورس كمكتمل
            return this.totalProgress;
        }
        
        // تحديث العرض العام
        this.updateOverallDisplay();
        
        return this.totalProgress;
    }
    
    updateModuleDisplay(module, progress) {
        const progressIndicator = module.element.querySelector('.module-progress-indicator');
        if (!progressIndicator) return;
        
        const progressFill = progressIndicator.querySelector('.module-progress-fill');
        const progressText = progressIndicator.querySelector('.module-progress-text');
        
        const percentage = progress.completionRate * 100;
        
        if (progressFill) {
            progressFill.style.width = percentage + '%';
            progressFill.style.backgroundColor = percentage >= 100 ? '#10b981' : '#3b82f6';
            progressFill.setAttribute('data-completed', percentage >= 100 ? 'true' : 'false');
        }
        
        if (progressText) {
            progressText.textContent = Math.round(percentage) + '%';
            progressText.style.color = percentage >= 100 ? '#10b981' : '#64748b';
        }
        
        // إضافة معلومات إضافية
        if (!progressIndicator.querySelector('.module-details')) {
            const details = document.createElement('div');
            details.className = 'module-details';
            details.style.cssText = `
                font-size: 0.65rem;
                color: #6b7280;
                margin-top: 2px;
                text-align: right;
            `;
            progressIndicator.appendChild(details);
        }
        
        const detailsElement = progressIndicator.querySelector('.module-details');
        detailsElement.textContent = `${progress.completed}/${progress.total} عناصر`;
    }
    
    updateOverallDisplay() {
        console.log(`🔄 Updating overall display: ${this.totalProgress.toFixed(1)}%`);
        
        // تحديث شريط التقدم في الـ sidebar
        const progressBar = document.querySelector('.progress-fill-sidebar');
        if (progressBar) {
            progressBar.style.width = this.totalProgress + '%';
            progressBar.setAttribute('data-progress', this.totalProgress);
            
            // إضافة تأثير بصري لشريط التقدم
            progressBar.style.boxShadow = '0 2px 12px rgba(0, 201, 255, 0.6)';
            setTimeout(() => {
                progressBar.style.boxShadow = '0 2px 8px rgba(0, 201, 255, 0.4)';
            }, 1000);
        }
        
        // تحديث النص
        const progressText = document.querySelector('.progress-title-sidebar .progress-text-content, .sidebar-progress-section, .course-progress-text');
        
        if (progressText) {
            const newText = progressText.innerHTML.replace(/تقدمك: \d+\.?\d*%/, `تقدمك: ${this.totalProgress.toFixed(1)}%`);
            progressText.innerHTML = newText;
            
            // إضافة تأثير بصري للنص
            progressText.style.textShadow = '0 0 10px rgba(255, 255, 255, 0.8)';
            progressText.style.transition = 'text-shadow 0.3s ease';
            setTimeout(() => {
                progressText.style.textShadow = '';
            }, 1000);
        }
        
        // إرسال التقدم إلى الخادم
        this.sendProgressToServer();
    }
    
    updateCompletionStats() {
        const totalElements = document.querySelectorAll('.content-item').length;
        const completedElements = document.querySelectorAll('.content-item.completed').length;
        const totalModules = this.modules.length;
        
        const stats = document.querySelectorAll('.completion-stats .stat-number');
        if (stats.length >= 3) {
            stats[0].textContent = completedElements; // مكتمل
            stats[1].textContent = totalElements; // إجمالي
            stats[2].textContent = totalModules; // وحدات
        }
        
        // تحديث معلومات التقدم المحسن
        this.updateEnhancedProgressInfo();
    }
    
    updateEnhancedProgressInfo() {
        const enhancedInfo = document.querySelector('.enhanced-progress-breakdown');
        if (enhancedInfo) {
            const formula = enhancedInfo.querySelector('.progress-formula small');
            const breakdown = enhancedInfo.querySelector('.module-breakdown small');
            
            if (formula) {
                formula.innerHTML = `
                    <i class="fas fa-calculator me-1"></i>
                    النظام: ${this.modules.length} موديول × 5 عناصر = ${this.modules.length * 5} عنصر إجمالي
                `;
            }
            
            if (breakdown && this.modules.length > 0) {
                const progressPerModule = 100 / this.modules.length;
                const progressPerElement = progressPerModule / 5;
                breakdown.innerHTML = `
                    كل موديول = ${progressPerModule.toFixed(1)}% | كل عنصر = ${progressPerElement.toFixed(1)}%
                `;
            }
        }
        
        // Also update main page percentages
        this.updateMainPagePercentages();
    }
    
    updateMainPagePercentages() {
        const modulePercentage = (100 / this.modules.length).toFixed(1);
        const elementPercentage = (100 / this.modules.length / 5).toFixed(1);
        const totalElements = this.modules.length * 5;
        
        // Update main page elements
        const moduleSpan = document.getElementById('module-percentage');
        const elementSpan = document.getElementById('element-percentage');
        
        if (moduleSpan) {
            moduleSpan.textContent = modulePercentage;
        }
        
        if (elementSpan) {
            elementSpan.textContent = elementPercentage;
        }
        
        // Update sidebar elements
        const sidebarModuleSpan = document.querySelector('.sidebar-module-percentage');
        const sidebarElementSpan = document.querySelector('.sidebar-element-percentage');
        const sidebarModuleCount = document.querySelector('.sidebar-module-count');
        const sidebarTotalElements = document.querySelector('.sidebar-total-elements');
        
        if (sidebarModuleSpan) {
            sidebarModuleSpan.textContent = modulePercentage;
        }
        
        if (sidebarElementSpan) {
            sidebarElementSpan.textContent = elementPercentage;
        }
        
        if (sidebarModuleCount) {
            sidebarModuleCount.textContent = this.modules.length;
        }
        
        if (sidebarTotalElements) {
            sidebarTotalElements.textContent = totalElements;
        }
    }
    
    sendProgressToServer() {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        const courseId = document.querySelector('meta[name="course-id"]')?.getAttribute('content');
        
        if (!csrfToken || !courseId) {
            console.warn('⚠️ CSRF token or course ID not found, skipping server update');
            return;
        }
        
        fetch(`/course/${courseId}/update-progress/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({
                progress: this.totalProgress,
                module_progress: this.modules.map(module => ({
                    id: module.id,
                    progress: this.calculateModuleProgress(module).completionRate * 100
                }))
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                console.log('✅ Progress updated on server:', this.totalProgress.toFixed(1) + '%');
            } else {
                console.error('❌ Server error:', data.message);
            }
        })
        .catch(error => {
            console.error('❌ Network error:', error);
        });
    }
    
    setupProgressTracking() {
        const observer = new MutationObserver((mutations) => {
            let shouldUpdate = false;
            
            mutations.forEach((mutation) => {
                if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                    const target = mutation.target;
                    if (target.classList.contains('content-item')) {
                        shouldUpdate = true;
                    }
                }
            });
            
            if (shouldUpdate) {
                console.log('🔄 Content completion state changed, recalculating progress...');
                setTimeout(async () => await this.calculateOverallProgress(), 500);
            }
        });
        
        // مراقبة جميع عناصر المحتوى
        document.querySelectorAll('.content-item').forEach(item => {
            observer.observe(item, { 
                attributes: true, 
                attributeFilter: ['class'] 
            });
        });
        
        console.log('👁️ Progress tracking observer set up');
    }
    
    setupPeriodicUpdate() {
        // تحديث دوري كل 30 ثانية
        setInterval(() => {
            console.log('⏱️ Periodic progress update');
            (async () => await this.calculateOverallProgress())();
        }, 30000);
    }
    
    // دالة لتعديل إكمال المحتوى يدوياً (للاختبار)
    markContentCompleted(contentType, contentId) {
        const selector = `.content-item[data-content-type="${contentType}"][data-content-id="${contentId}"]`;
        const element = document.querySelector(selector);
        
        if (element) {
            element.classList.add('completed');
            console.log(`✅ Manually marked ${contentType} ${contentId} as completed`);
            
            setTimeout(async () => await this.calculateOverallProgress(), 300);
            return true;
        }
        
        console.warn(`⚠️ Content not found: ${contentType} ${contentId}`);
        return false;
    }
    
    // دالة لتحميل الإكمال المحفوظ من localStorage
    loadStoredCompletions() {
        console.log('💾 Loading stored completions from localStorage...');
        
        const allContentItems = document.querySelectorAll('.content-item');
        let loadedCount = 0;
        
        allContentItems.forEach(item => {
            const contentType = item.getAttribute('data-content-type');
            const contentId = item.getAttribute('data-content-id');
            
            if (contentType && contentId) {
                const completionKey = `completed_${contentType}_${contentId}`;
                const isCompleted = localStorage.getItem(completionKey);
                
                if (isCompleted === 'true') {
                    item.classList.add('completed');
                    
                    // إضافة badge للإكمال إذا لم يكن موجوداً
                    if (!item.querySelector('.completion-badge')) {
                        const badge = document.createElement('div');
                        badge.className = 'completion-badge';
                        badge.innerHTML = '<i class="fas fa-check"></i>';
                        badge.style.cssText = `
                            background: #28a745;
                            color: white;
                            padding: 4px 8px;
                            border-radius: 50%;
                            font-size: 0.8rem;
                            position: absolute;
                            right: 10px;
                            top: 50%;
                            transform: translateY(-50%);
                        `;
                        item.style.position = 'relative';
                        item.appendChild(badge);
                    }
                    
                    loadedCount++;
                    console.log(`✅ Loaded completion for ${contentType} ${contentId}`);
                    
                    // تحديث الأزرار إذا كانت مرئية
                    this.updateCompletionButton(contentType, contentId);
                }
            }
        });
        
        console.log(`📥 Loaded ${loadedCount} completed items from localStorage`);
    }
    
    // دالة لتحديث حالة أزرار الإكمال
    updateCompletionButton(contentType, contentId) {
        // تحديث زر PDF
        if (contentType === 'module_pdf') {
            const button = document.querySelector(`.mark-pdf-read-btn[data-content-id="${contentId}"]`);
            if (button) {
                button.classList.remove('btn-info');
                button.classList.add('btn-success');
                button.innerHTML = '<i class="fas fa-check me-2"></i>مكتمل';
                button.disabled = true;
            }
        }
        
        // تحديث زر الملاحظات
        if (contentType === 'module_note') {
            const button = document.querySelector(`.mark-note-read-btn[data-content-id="${contentId}"]`);
            if (button) {
                button.classList.remove('btn-info');
                button.classList.add('btn-success');
                button.innerHTML = '<i class="fas fa-check me-2"></i>مكتمل';
                button.disabled = true;
            }
        }
    }

    // دالة للحصول على تقرير التقدم التفصيلي
    getProgressReport() {
        const report = {
            totalProgress: this.totalProgress,
            modules: this.modules.map(module => {
                const progress = this.calculateModuleProgress(module);
                return {
                    name: module.name,
                    id: module.id,
                    completionRate: progress.completionRate,
                    completedElements: progress.completed,
                    totalElements: progress.total,
                    progressPoints: progress.progressPoints,
                    elements: Object.keys(module.elements).map(type => ({
                        type: type,
                        exists: !!module.elements[type],
                        completed: module.elements[type]?.classList.contains('completed') || false
                    }))
                };
            })
        };
        
        console.table(report.modules);
        return report;
    }
    
    // دالة للتحقق من الامتحان النهائي من قاعدة البيانات
    async checkFinalExamFromDatabase() {
        console.log('🎓 Checking final exam completion from database...');
        
        // الحصول على course ID من عدة مصادر
        let courseId = this.courseId;
        if (!courseId) {
            // محاولة الحصول عليه من URL
            const urlMatch = window.location.pathname.match(/\/courseviewpage\/(\d+)\//);
            if (urlMatch) {
                courseId = urlMatch[1];
            }
        }
        if (!courseId) {
            // محاولة الحصول عليه من meta tag
            const metaTag = document.querySelector('meta[name="course-id"]');
            if (metaTag) {
                courseId = metaTag.getAttribute('content');
            }
        }
        
        if (!courseId) {
            console.warn('⚠️ Course ID not found for final exam check');
            return false;
        }
        
        console.log(`🆔 Using course ID: ${courseId}`);
        this.courseId = courseId; // حفظ للاستخدام المستقبلي
        
        try {
            const response = await fetch(`/api/course/${courseId}/check-final-exam/`, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('📊 Final exam check response:', data);
            
            if (data.status === 'success' && data.course_completed) {
                console.log('🎉 Final exam passed! Setting progress to 100%');
                
                // تحديث التقدم إلى 100%
                this.totalProgress = 100.0;
                
                // تحديث العرض
                this.updateProgressDisplay();
                
                // إظهار رسالة تهنئة
                this.showCelebrationMessage('🎉 تهانينا! لقد أكملت الدورة بنجاح بعد اجتياز الامتحان النهائي!');
                
                // تحديث حالة اكتمال الكورس
                this.markCourseAsCompleted();
                
                return true;
            }
            
            return false;
            
        } catch (error) {
            console.error('❌ Error checking final exam from database:', error);
            return false;
        }
    }
    
    // دالة لتحديث العرض فقط بدون إعادة حساب
    updateProgressDisplay() {
        console.log(`🎯 Updating progress display: ${this.totalProgress.toFixed(1)}%`);
        
        // تحديث شريط التقدم
        const progressBar = document.querySelector('.progress-fill-sidebar');
        if (progressBar) {
            progressBar.style.width = this.totalProgress + '%';
            progressBar.setAttribute('data-progress', this.totalProgress);
            
            // تأثير بصري مميز للإكمال
            if (this.totalProgress >= 100) {
                progressBar.style.background = 'linear-gradient(90deg, #28a745 0%, #20c997 100%)';
                progressBar.style.boxShadow = '0 2px 15px rgba(40, 167, 69, 0.8)';
            } else {
                progressBar.style.background = 'linear-gradient(90deg, #00c9ff 0%, #92fe9d 100%)';
                progressBar.style.boxShadow = '0 2px 12px rgba(0, 201, 255, 0.6)';
            }
            
            setTimeout(() => {
                progressBar.style.boxShadow = this.totalProgress >= 100 ? 
                    '0 2px 8px rgba(40, 167, 69, 0.4)' : 
                    '0 2px 8px rgba(0, 201, 255, 0.4)';
            }, 1000);
        }
        
        // تحديث النص
        const progressText = document.querySelector('.progress-title-sidebar .progress-text-content, .sidebar-progress-section, .course-progress-text');
        if (progressText) {
            const newText = progressText.innerHTML.replace(/تقدمك: \d+\.?\d*%/, `تقدمك: ${this.totalProgress.toFixed(1)}%`);
            progressText.innerHTML = newText;
            
            // تأثير بصري للنص
            progressText.style.textShadow = '0 0 10px rgba(255, 255, 255, 0.8)';
            progressText.style.transition = 'text-shadow 0.3s ease';
            
            // لون مميز للإكمال
            if (this.totalProgress >= 100) {
                progressText.style.color = '#28a745';
                progressText.style.fontWeight = 'bold';
            }
            
            setTimeout(() => {
                progressText.style.textShadow = '';
            }, 1000);
        }
    }
    
    // دالة لتسجيل اكتمال الكورس على الخادم
    async markCourseAsCompleted() {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        const courseId = this.courseId;
        
        if (!csrfToken || !courseId) {
            console.warn('⚠️ CSRF token or course ID not found for course completion');
            return;
        }
        
        try {
            const response = await fetch(`/api/course/${courseId}/complete/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    progress: this.totalProgress,
                    completed: true,
                    final_exam_passed: true
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            if (data.status === 'success') {
                console.log('✅ Course marked as completed on server');
                this.updateCompletionButtons();
            } else {
                console.error('❌ Server error completing course:', data.message);
            }
            
        } catch (error) {
            console.error('❌ Network error completing course:', error);
        }
    }
    
    // دالة لتحديث أزرار الإكمال
    updateCompletionButtons() {
        // البحث عن أزرار الإكمال
        const completeButton = document.querySelector('.nav-complete');
        const completedButton = document.querySelector('.nav-completed');
        
        // إخفاء زر الإكمال وإظهار زر "مكتملة"
        if (completeButton) completeButton.style.display = 'none';
        if (completedButton) {
            completedButton.style.display = 'block';
            completedButton.classList.remove('d-none');
        } else {
            // إنشاء زر "مكتملة" إذا لم يكن موجوداً
            this.createCompletedButton();
        }
    }
    
    // دالة لإنشاء زر "مكتملة"
    createCompletedButton() {
        const navigationControls = document.querySelector('.navigation-controls');
        if (!navigationControls) return;
        
        const completedButton = document.createElement('button');
        completedButton.className = 'nav-btn nav-completed btn btn-success';
        completedButton.disabled = true;
        completedButton.innerHTML = '<i class="fas fa-check-circle"></i> مكتملة بنجاح';
        
        const completionSection = navigationControls.querySelector('.completion-section') || navigationControls;
        completionSection.appendChild(completedButton);
    }
    
    // دالة لإظهار رسالة احتفالية
    showCelebrationMessage(message) {
        const celebration = document.createElement('div');
        celebration.className = 'alert alert-success position-fixed celebration-alert';
        celebration.style.cssText = `
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 9999;
            max-width: 500px;
            text-align: center;
            animation: celebrationPulse 2s ease-in-out;
            box-shadow: 0 8px 32px rgba(40, 167, 69, 0.3);
        `;
        celebration.innerHTML = `
            <div class="d-flex align-items-center justify-content-center">
                <span style="font-size: 1.2rem; font-weight: bold;">${message}</span>
            </div>
        `;
        
        document.body.appendChild(celebration);
        
        // إزالة تلقائية بعد 5 ثوانِ
        setTimeout(() => {
            if (celebration.parentElement) {
                celebration.remove();
            }
        }, 5000);
        
        // إضافة CSS للانيميشن
        if (!document.getElementById('celebration-styles')) {
            const style = document.createElement('style');
            style.id = 'celebration-styles';
            style.textContent = `
                @keyframes celebrationPulse {
                    0% { transform: translateX(-50%) scale(0.8); opacity: 0; }
                    50% { transform: translateX(-50%) scale(1.05); opacity: 1; }
                    100% { transform: translateX(-50%) scale(1); opacity: 1; }
                }
            `;
            document.head.appendChild(style);
        }
    }
}

// تهيئة النظام عند تحميل الصفحة
document.addEventListener('DOMContentLoaded', function() {
    // إنتظار تحميل العناصر بالكامل
    setTimeout(async () => {
        window.enhancedProgressSystem = new EnhancedProgressSystem();
        await window.enhancedProgressSystem.init();
        
        // ربط الدوال بالنافذة العامة للوصول إليها من ملفات أخرى
        window.updateOverallProgress = async () => await window.enhancedProgressSystem.calculateOverallProgress();
        window.getProgressReport = () => window.enhancedProgressSystem.getProgressReport();
        window.markContentCompleted = (type, id) => window.enhancedProgressSystem.markContentCompleted(type, id);
        
        console.log('🎯 Enhanced Progress System ready!');
    }, 1500);
});

// تصدير الكلاس للاستخدام في ملفات أخرى
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EnhancedProgressSystem;
} 