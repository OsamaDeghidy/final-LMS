    // Accordion functionality
    document.querySelectorAll('.accordion-header').forEach(header => {
        header.addEventListener('click', () => {
            const item = header.parentElement;
            item.classList.toggle('active');
        });
    });

    // Tab functionality
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelector('.tab.active').classList.remove('active');
            tab.classList.add('active');
        });
    });

    // Course card hover effect
    document.querySelectorAll('.course-card').forEach(card => {
        card.addEventListener('mouseenter', () => {
            card.style.boxShadow = '0 10px 20px rgba(0, 0, 0, 0.1)';
        });
        card.addEventListener('mouseleave', () => {
            card.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.08), 0 4px 12px rgba(0, 0, 0, 0.08)';
        });
    });


document.addEventListener('DOMContentLoaded', function() {
    // Main Tab switching functionality
    const tabs = document.querySelectorAll('.tab');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // Remove active class from all tabs
            tabs.forEach(t => t.classList.remove('active'));
            
            // Add active class to clicked tab
            this.classList.add('active');
            
            // Hide all tab contents
            tabContents.forEach(content => {
                content.style.display = 'none';
            });
            
            // Show the corresponding tab content
            const tabId = this.getAttribute('data-tab');
            document.getElementById(tabId + '-tab').style.display = 'block';
        });
    });
    
    // Content Sub-tabs functionality
    const subtabs = document.querySelectorAll('.subtab');
    const subtabContents = document.querySelectorAll('.subtab-content');
    
    subtabs.forEach(subtab => {
        subtab.addEventListener('click', function() {
            // Remove active class from all subtabs
            subtabs.forEach(t => t.classList.remove('active'));
            
            // Add active class to clicked subtab
            this.classList.add('active');
            
            // Hide all subtab contents
            subtabContents.forEach(content => {
                content.style.display = 'none';
            });
            
            // Show the corresponding subtab content
            const subtabId = this.getAttribute('data-subtab');
            document.getElementById(subtabId + '-subtab').style.display = 'block';
        });
    });
    
    // FAQ toggle functionality
    const faqQuestions = document.querySelectorAll('.faq-question');
    
    faqQuestions.forEach(question => {
        question.addEventListener('click', function() {
            const answer = this.nextElementSibling;
            if (answer.style.display === 'none' || !answer.style.display) {
                answer.style.display = 'block';
            } else {
                answer.style.display = 'none';
            }
        });
    });
});