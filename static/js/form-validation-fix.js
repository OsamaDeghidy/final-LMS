// Add this to course-update.js
document.addEventListener('DOMContentLoaded', function() {
    // Add event listener to the "Submit" button
    const submitBtn = document.getElementById('submit-course-btn');
    if (submitBtn) {
        submitBtn.addEventListener('click', function(e) {
            e.preventDefault();
            submitCourse();
        });
    }
});

// Submit the course form
function submitCourse() {
    if (validateForm()) {
        document.getElementById('course-form').submit();
    }
}

function validateForm() {
    // Validate required fields that are visible (not in hidden steps)
    const visibleSteps = document.querySelectorAll('.step-card:not(.d-none)');
    let isValid = true;
    
    visibleSteps.forEach(step => {
        const requiredFields = step.querySelectorAll('[required]');
        
        requiredFields.forEach(field => {
            if (!field.value) {
                field.classList.add('is-invalid');
                isValid = false;
            } else {
                field.classList.remove('is-invalid');
            }
        });
    });
    
    if (!isValid) {
        alert('يرجى ملء جميع الحقول المطلوبة');
        return false;
    }
    
    // Check if at least one module is added
    if (document.querySelectorAll('.module-card').length === 0) {
        alert('يرجى إضافة موديول واحد على الأقل');
        return false;
    }
    
    return true;
}
