// Function to open the delete course modal
function openDeleteCourseModal(courseId, courseName) {
    const modal = document.getElementById('deleteCourseModal');
    const courseNameElement = document.getElementById('courseNameToDelete');
    const confirmButton = document.getElementById('confirmDeleteButton');
    
    // Set the course name in the modal
    courseNameElement.textContent = courseName;
    
    // Update the confirm button's onclick handler
    confirmButton.onclick = function() {
        deleteCourse(courseId);
    };
    
    // Show the modal
    modal.classList.add('show');
    modal.style.display = 'block';
    document.body.classList.add('modal-open');
    
    // Add a backdrop
    const backdrop = document.createElement('div');
    backdrop.className = 'modal-backdrop fade show';
    document.body.appendChild(backdrop);
}

// Function to close the delete course modal
function closeDeleteCourseModal() {
    const modal = document.getElementById('deleteCourseModal');
    modal.classList.remove('show');
    modal.style.display = 'none';
    document.body.classList.remove('modal-open');
    
    // Remove the backdrop
    const backdrop = document.querySelector('.modal-backdrop');
    if (backdrop) {
        backdrop.remove();
    }
}

// Function to delete a course
function deleteCourse(courseId) {
    // Get the CSRF token
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    // Send a DELETE request to the server
    fetch(`/courses/delete/${courseId}/`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': csrftoken,
            'Content-Type': 'application/json'
        },
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Close the modal
            closeDeleteCourseModal();
            // Show success message
            showAlert('تم حذف الكورس بنجاح', 'success');
            // Remove the course card from the DOM
            const courseCard = document.getElementById(`course-${courseId}`);
            if (courseCard) {
                courseCard.remove();
            }
        } else {
            throw new Error(data.message || 'حدث خطأ أثناء حذف الكورس');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert(error.message || 'حدث خطأ أثناء حذف الكورس', 'danger');
    });
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
    // Initialize tooltips and popovers
    initializeTooltips();
    initializePopovers();
    
    // Add event listeners for the delete course modal
    const modal = document.getElementById('deleteCourseModal');
    if (modal) {
        // Close modal when clicking the close button
        const closeButtons = modal.querySelectorAll('[data-bs-dismiss="modal"]');
        closeButtons.forEach(button => {
            button.addEventListener('click', closeDeleteCourseModal);
        });
        
        // Close modal when clicking outside
        modal.addEventListener('click', function(event) {
            if (event.target === modal) {
                closeDeleteCourseModal();
            }
        });
    }
});
