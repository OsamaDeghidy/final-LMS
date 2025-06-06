/**
 * Attendance tracking for video viewing
 * This script automatically tracks attendance when a user watches videos
 */

// Track if the user is currently watching a video
let isWatching = false;
let attendanceId = null;
let videoId = null;

// Initialize attendance tracking when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Find the video element
    const videoElement = document.getElementById('course-video');
    
    if (videoElement) {
        initializeAttendanceTracking(videoElement);
    }
});

/**
 * Initialize attendance tracking for a video element
 * @param {HTMLVideoElement} videoElement - The video element to track
 */
function initializeAttendanceTracking(videoElement) {
    // Get video and course IDs from data attributes
    const videoId = videoElement.getAttribute('data-video-id');
    const courseId = videoElement.getAttribute('data-course-id');
    
    if (!videoId || !courseId) {
        console.error('Video or course ID not found on video element');
        return;
    }
    
    let attendanceId = null;
    let isAttendanceMarked = false;
    
    // Event: Video starts playing
    videoElement.addEventListener('play', function() {
        if (!isAttendanceMarked) {
            markAttendanceIn(videoId);
        }
    });
    
    // Event: Video ends
    videoElement.addEventListener('ended', function() {
        if (isAttendanceMarked && attendanceId) {
            markAttendanceOut(attendanceId);
            isAttendanceMarked = false;
        }
    });
    
    // Event: User leaves the page
    window.addEventListener('beforeunload', function() {
        if (isAttendanceMarked && attendanceId) {
            markAttendanceOut(attendanceId);
        }
    });
    
    /**
     * Mark attendance in (start time)
     * @param {string} videoId - The ID of the video being watched
     */
    function markAttendanceIn(videoId) {
        // Get CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        fetch('/attendance/auto-track/' + videoId + '/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                action: 'in'
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                console.log('Attendance marked: IN');
                attendanceId = data.attendance_id;
                isAttendanceMarked = true;
            } else {
                console.error('Error marking attendance:', data.message);
            }
        })
        .catch(error => {
            console.error('Error marking attendance:', error);
        });
    }
    
    /**
     * Mark attendance out (end time)
     * @param {string} attendanceId - The ID of the attendance record
     */
    function markAttendanceOut(attendanceId) {
        // Get CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        fetch('/attendance/mark-out/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                attendance_id: attendanceId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                console.log('Attendance marked: OUT');
                attendanceId = null;
            } else {
                console.error('Error marking attendance out:', data.message);
            }
        })
        .catch(error => {
            console.error('Error marking attendance out:', error);
        });
    }
}
