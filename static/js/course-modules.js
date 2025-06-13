/**
 * Course Modules Management
 * Handles module toggle functionality and content navigation
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeModules();
    setupModuleToggle();
    setupContentNavigation();
});

/**
 * Initialize modules - open first module and current content module by default
 */
function initializeModules() {
    // Open first module by default
    const firstModule = document.querySelector('.module-content');
    const firstIcon = document.querySelector('.toggle-icon');
    
    if (firstModule && firstIcon) {
        firstModule.classList.add('active');
        firstIcon.classList.remove('rotated');
    }
    
    // Open module containing current content
    const currentContent = document.querySelector('.content-item.current');
    if (currentContent) {
        const currentModule = currentContent.closest('.module-content');
        if (currentModule && currentModule !== firstModule) {
            currentModule.classList.add('active');
            const moduleId = currentModule.id;
            const icon = document.getElementById('icon-' + moduleId);
            if (icon) {
                icon.classList.remove('rotated');
            }
        }
    }
}

/**
 * Setup module toggle functionality
 */
function setupModuleToggle() {
    // Make toggleModule function available globally
    window.toggleModule = function(moduleId) {
        const moduleContent = document.getElementById(moduleId);
        const icon = document.getElementById('icon-' + moduleId);
        
        if (moduleContent && icon) {
            if (moduleContent.classList.contains('active')) {
                // Close module
                moduleContent.classList.remove('active');
                icon.classList.add('rotated');
                
                // Add closing animation
                moduleContent.style.maxHeight = moduleContent.scrollHeight + 'px';
                setTimeout(() => {
                    moduleContent.style.maxHeight = '0';
                }, 10);
            } else {
                // Open module
                moduleContent.classList.add('active');
                icon.classList.remove('rotated');
                
                // Add opening animation
                moduleContent.style.maxHeight = 'none';
                const height = moduleContent.scrollHeight;
                moduleContent.style.maxHeight = '0';
                setTimeout(() => {
                    moduleContent.style.maxHeight = height + 'px';
                    setTimeout(() => {
                        moduleContent.style.maxHeight = 'none';
                    }, 300);
                }, 10);
            }
        }
    };
}

/**
 * Setup content navigation and tracking
 */
function setupContentNavigation() {
    const contentItems = document.querySelectorAll('.content-item');
    
    contentItems.forEach(item => {
        item.addEventListener('click', function(e) {
            // Remove current class from all items
            contentItems.forEach(otherItem => {
                otherItem.classList.remove('current');
            });
            
            // Add current class to clicked item
            this.classList.add('current');
            
            // Update progress indicator
            updateProgressIndicator(this);
        });
    });
}

/**
 * Update progress indicator in sidebar
 */
function updateProgressIndicator(clickedItem) {
    const indicator = document.querySelector('.current-position-indicator');
    if (!indicator) return;
    
    const contentInfo = indicator.querySelector('.current-content-info');
    if (!contentInfo) return;
    
    const contentType = clickedItem.dataset.contentType;
    const contentName = clickedItem.querySelector('.content-name').textContent;
    
    let icon = '';
    switch(contentType) {
        case 'module_video':
        case 'video':
            icon = '<i class="fas fa-play-circle text-primary me-1"></i>';
            break;
        case 'module_pdf':
        case 'note':
            icon = '<i class="fas fa-file-pdf text-danger me-1"></i>';
            break;
        case 'module_note':
            icon = '<i class="fas fa-sticky-note text-info me-1"></i>';
            break;
        case 'quiz':
            icon = '<i class="fas fa-question-circle text-warning me-1"></i>';
            break;
        case 'assignment':
            icon = '<i class="fas fa-tasks text-success me-1"></i>';
            break;
        case 'exam':
            icon = '<i class="fas fa-graduation-cap text-primary me-1"></i>';
            break;
        default:
            icon = '<i class="fas fa-file me-1"></i>';
    }
    
    contentInfo.innerHTML = icon + contentName.substring(0, 30) + (contentName.length > 30 ? '...' : '');
}

/**
 * Smooth scroll to active content
 */
function scrollToActiveContent() {
    const activeContent = document.querySelector('.content-item.current');
    if (activeContent) {
        activeContent.scrollIntoView({
            behavior: 'smooth',
            block: 'center'
        });
    }
}

/**
 * Toggle all modules (expand/collapse all)
 */
function toggleAllModules(expand = true) {
    const modules = document.querySelectorAll('.module-content');
    const icons = document.querySelectorAll('.toggle-icon');
    
    modules.forEach((module, index) => {
        const icon = icons[index];
        if (expand) {
            module.classList.add('active');
            if (icon) icon.classList.remove('rotated');
        } else {
            module.classList.remove('active');
            if (icon) icon.classList.add('rotated');
        }
    });
}

/**
 * Get module progress statistics
 */
function getModuleProgress(moduleId) {
    const module = document.getElementById(moduleId);
    if (!module) return null;
    
    const totalItems = module.querySelectorAll('.content-item').length;
    const completedItems = module.querySelectorAll('.content-item.completed').length;
    
    return {
        total: totalItems,
        completed: completedItems,
        percentage: totalItems > 0 ? (completedItems / totalItems) * 100 : 0
    };
}

/**
 * Update module progress display
 */
function updateModuleProgressDisplay() {
    const moduleHeaders = document.querySelectorAll('.module-header');
    
    moduleHeaders.forEach(header => {
        const moduleContent = header.nextElementSibling;
        if (!moduleContent) return;
        
        const progress = getModuleProgress(moduleContent.id);
        if (!progress) return;
        
        let progressBadge = header.querySelector('.module-progress-badge');
        if (!progressBadge) {
            progressBadge = document.createElement('span');
            progressBadge.className = 'module-progress-badge';
            header.appendChild(progressBadge);
        }
        
        if (progress.percentage === 100) {
            progressBadge.innerHTML = '<i class="fas fa-check-circle text-success"></i>';
            progressBadge.title = 'مكتملة';
        } else if (progress.percentage > 0) {
            progressBadge.innerHTML = `<span class="text-warning">${Math.round(progress.percentage)}%</span>`;
            progressBadge.title = `${progress.completed} من ${progress.total} مكتمل`;
        } else {
            progressBadge.innerHTML = '<i class="far fa-circle text-muted"></i>';
            progressBadge.title = 'لم تبدأ بعد';
        }
    });
}

// Export functions for external use
window.CourseModules = {
    toggleModule: window.toggleModule,
    toggleAllModules,
    scrollToActiveContent,
    getModuleProgress,
    updateModuleProgressDisplay
}; 