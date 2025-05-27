/**
 * All Courses Page JavaScript
 * Handles functionality for the courses listing page
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize any necessary components when the DOM is fully loaded
    initCourseSearch();
    // Add more initialization functions here as needed
});

/**
 * Initialize course search functionality
 */
function initCourseSearch() {
    const searchInput = document.querySelector('.search-input');
    const searchButton = document.querySelector('.search-btn');
    
    if (searchInput && searchButton) {
        // Handle search button click
        searchButton.addEventListener('click', function(e) {
            e.preventDefault();
            performSearch(searchInput.value.trim());
        });
        
        // Handle Enter key in search input
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                performSearch(this.value.trim());
            }
        });
    }
}

/**
 * Perform search with the given query
 * @param {string} query - The search query
 */
function performSearch(query) {
    if (query) {
        // Here you would typically make an AJAX call to your backend
        // For now, we'll just submit the form
        const form = document.createElement('form');
        form.method = 'GET';
        form.action = window.location.pathname;
        
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'q';
        input.value = query;
        
        form.appendChild(input);
        document.body.appendChild(form);
        form.submit();
    }
}

/**
 * Add course to wishlist
 * @param {number} courseId - The ID of the course to add to wishlist
 */
function addToWishlist(courseId) {
    // Implementation for adding course to wishlist
    console.log(`Adding course ${courseId} to wishlist`);
    // Add your AJAX call here to update the wishlist
}

/**
 * Toggle course enrollment status
 * @param {number} courseId - The ID of the course to enroll in
 */
function toggleEnrollment(courseId) {
    // Implementation for course enrollment
    console.log(`Toggling enrollment for course ${courseId}`);
    // Add your AJAX call here to handle enrollment
}

// Add more course-related functions as needed
