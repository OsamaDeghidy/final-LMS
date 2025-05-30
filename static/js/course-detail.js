    document.addEventListener('DOMContentLoaded', function() {
    // Main Tab switching functionality
    const tabs = document.querySelectorAll('.course-tabs .tab');
    const tabContents = document.querySelectorAll('.tab-content');
    
    // Set initial state - ensure first tab is active and its content is shown
    if (tabs.length > 0) {
        // Make first tab active
        tabs[0].classList.add('active');
        
        // Show first tab content
        const firstTabId = tabs[0].getAttribute('data-tab');
        const firstTabContent = document.getElementById(firstTabId + '-tab');
        if (firstTabContent) {
            firstTabContent.style.display = 'block';
        }
    }
    
    // Add click event to each tab
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
            
            const tabId = this.getAttribute('data-tab');
            const tabContent = document.getElementById(tabId + '-tab');
            if (tabContent) {
                tabContent.style.display = 'block';
                
                // If this is the content tab, initialize subtabs
                if (tabId === 'content') {
                    initializeSubtabs();
                }
            }
        });
    });
    
    // Function to initialize subtabs
    function initializeSubtabs() {
        const subtabs = document.querySelectorAll('.content-subtabs .subtab');
        const subtabContents = document.querySelectorAll('.subtab-content');
        
        // Set initial state for subtabs
        if (subtabs.length > 0) {
            // Make first subtab active
            subtabs.forEach(t => t.classList.remove('active'));
            subtabs[0].classList.add('active');
            
            // Show first subtab content, hide others
            subtabContents.forEach(content => {
                content.style.display = 'none';
            });
            
            const firstSubtabId = subtabs[0].getAttribute('data-subtab');
            const firstSubtabContent = document.getElementById(firstSubtabId + '-subtab');
            if (firstSubtabContent) {
                firstSubtabContent.style.display = 'block';
            }
        }
        
        // Add click event to each subtab
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
                const subtabContent = document.getElementById(subtabId + '-subtab');
                if (subtabContent) {
                    subtabContent.style.display = 'block';
                }
            });
        });
    }
    
    // Initialize subtabs if content tab is active on page load
    if (document.querySelector('.tab.active[data-tab="content"]')) {
        initializeSubtabs();
    }
    
    // FAQ toggle functionality
    const faqItems = document.querySelectorAll('.faq-item');
    faqItems.forEach(item => {
        const question = item.querySelector('.faq-question');
        if (question) {
            question.addEventListener('click', function() {
                const answer = item.querySelector('.faq-answer');
                if (answer) {
                    if (answer.style.display === 'none' || !answer.style.display || answer.style.display === '') {
                        answer.style.display = 'block';
                    } else {
                        answer.style.display = 'none';
                    }
                }
            });
        }
    });
    
    // Accordion functionality (if present)
    document.querySelectorAll('.accordion-header').forEach(header => {
        header.addEventListener('click', () => {
            const item = header.parentElement;
            item.classList.toggle('active');
        });
    });
    
    // Course card hover effect (if present)
    document.querySelectorAll('.course-card').forEach(card => {
        card.addEventListener('mouseenter', () => {
            card.style.boxShadow = '0 10px 20px rgba(0, 0, 0, 0.1)';
        });
        card.addEventListener('mouseleave', () => {
            card.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.08), 0 4px 12px rgba(0, 0, 0, 0.08)';
        });
    });
});