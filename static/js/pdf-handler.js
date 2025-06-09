/**
 * PDF Handler Script
 * Handles PDF viewing, marking as read, and progress tracking
 */

document.addEventListener('DOMContentLoaded', function() {
    // Setup PDF marking buttons
    setupPdfMarkingButtons();
});

/**
 * Sets up event listeners for PDF "mark as read" buttons
 */
function setupPdfMarkingButtons() {
    document.querySelectorAll('.mark-pdf-read-btn').forEach(button => {
        button.addEventListener('click', function() {
            // Determine PDF type (module or note)
            const pdfId = this.dataset.pdfId;
            const noteId = this.dataset.noteId;
            const courseId = this.dataset.courseId;
            
            let contentType, contentId;
            
            if (pdfId) {
                contentType = 'pdf';
                contentId = pdfId;
            } else if (noteId) {
                contentType = 'note';
                contentId = noteId;
            } else {
                console.error('لم يتم تحديد معرف PDF');
                return;
            }
            
            // Change button state
            this.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>جاري التحديث...';
            this.disabled = true;
            
            const csrfToken = getCookie('csrftoken');
            
            // Call API to mark content as viewed
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
                    // Update button
                    this.innerHTML = '<i class="fas fa-check-circle me-2"></i>تمت القراءة';
                    this.classList.remove('btn-info');
                    this.classList.add('btn-success');
                    this.disabled = true;
                    
                    // Update progress bar
                    if (data.progress !== undefined) {
                        updateProgressBar(data.progress);
                    } else {
                        updateProgress();
                    }
                    
                    // Add completion class to sidebar item
                    const sidebarItem = document.querySelector(`[data-content-id="${contentId}"][data-content-type="${contentType}"]`);
                    if (sidebarItem) {
                        sidebarItem.classList.add('completed');
                        const icon = sidebarItem.querySelector('.content-icon i');
                        if (icon) {
                            icon.className = 'fas fa-check';
                        }
                        
                        // Add completion badge
                        if (!sidebarItem.querySelector('.completion-badge')) {
                            const badge = document.createElement('div');
                            badge.className = 'completion-badge';
                            badge.innerHTML = '<i class="fas fa-check"></i>';
                            sidebarItem.appendChild(badge);
                        }
                    }
                    
                    // Show success message
                    showMessage('تم تحديد الملف كمقروء بنجاح', 'success');
                    
                    // Update completion counter
                    updateCompletionCounter();
                } else {
                    // Reset button to original state
                    this.innerHTML = '<i class="fas fa-check-circle me-2"></i>تحديد كمقروء';
                    this.disabled = false;
                    
                    // Show error message
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

/**
 * Helper function to get cookie value by name
 * This ensures the function is available if not already defined
 */
function getCookie(name) {
    if (window.getCookie && typeof window.getCookie === 'function') {
        return window.getCookie(name);
    }
    
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

/**
 * Helper function to show messages if not already defined
 */
function showMessage(message, type) {
    if (window.showMessage && typeof window.showMessage === 'function') {
        window.showMessage(message, type);
        return;
    }
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.top = '20px';
    alertDiv.style.right = '20px';
    alertDiv.style.zIndex = '9999';
    
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => alertDiv.remove(), 300);
    }, 3000);
}
