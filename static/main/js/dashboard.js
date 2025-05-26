// Global variable to store the current course ID for deletion
let courseIdToDelete = null;

// Function to open the delete course modal
function openDeleteCourseModal(courseId, courseName) {
    // Store the course ID for later use
    courseIdToDelete = courseId;
    
    // Update the course name in the modal
    const courseNameElement = document.getElementById('courseNameToDelete');
    if (courseNameElement) {
        courseNameElement.textContent = courseName;
    }
    
    // Show the modal
    const modal = new bootstrap.Modal(document.getElementById('deleteCourseModal'));
    modal.show();
}

// Function to close the delete course modal
function closeDeleteCourseModal() {
    // Try to get the modal instance using Bootstrap's API
    try {
        const modalElement = document.getElementById('deleteCourseModal');
        const bsModal = bootstrap.Modal.getInstance(modalElement);
        if (bsModal) {
            bsModal.hide();
            return;
        }
    } catch (error) {
        console.error('Error using Bootstrap Modal API:', error);
    }
    
    // Fallback method if Bootstrap API fails
    const modalElement = document.getElementById('deleteCourseModal');
    if (modalElement) {
        modalElement.classList.remove('show');
        modalElement.style.display = 'none';
        document.body.classList.remove('modal-open');
        
        // Remove the backdrop
        const backdrop = document.querySelector('.modal-backdrop');
        if (backdrop) {
            backdrop.remove();
        }
    }
}

// Function to delete a course
function deleteCourse() {
    // Check if we have a course ID to delete
    if (!courseIdToDelete) {
        alert('No course ID found for deletion');
        return;
    }
    
    // Create a form to submit
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/course/delete/';
    
    // Add CSRF token
    const csrfInput = document.createElement('input');
    csrfInput.type = 'hidden';
    csrfInput.name = 'csrfmiddlewaretoken';
    csrfInput.value = document.querySelector('[name=csrfmiddlewaretoken]').value;
    form.appendChild(csrfInput);
    
    // Add course ID
    const courseIdInput = document.createElement('input');
    courseIdInput.type = 'hidden';
    courseIdInput.name = 'course_id';
    courseIdInput.value = courseIdToDelete;
    form.appendChild(courseIdInput);
    
    // Add to document and submit
    document.body.appendChild(form);
    form.submit();
}

// Function to show alerts
function showAlert(message, type) {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add the alert to the page
    const container = document.querySelector('.container.my-4') || document.body;
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const alert = bootstrap.Alert.getOrCreateInstance(alertDiv);
        if (alert) {
            alert.close();
        }
    }, 5000);
}

// Initialize tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Initialize popovers
function initializePopovers() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

// Initialize the dashboard when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initialized');
    
    // Initialize tooltips and popovers
    initializeTooltips();
    initializePopovers();
    
    // Add event listeners for the delete course modal
    const modal = document.getElementById('deleteCourseModal');
    if (modal) {
        console.log('Delete course modal found');
        
        // Add event listeners for close buttons
        const closeButtons = modal.querySelectorAll('[data-bs-dismiss="modal"]');
        closeButtons.forEach(button => {
            button.addEventListener('click', function() {
                closeDeleteCourseModal();
            });
        });
    } else {
        console.error('Delete course modal not found');
    }
});
