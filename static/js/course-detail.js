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

    // Enroll buttons
    document.querySelectorAll('.sidebar-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            alert('تمت إضافة الدورة إلى سلة التسوق الخاصة بك!');
        });
    });

    // Write review button
    document.querySelector('.write-review').addEventListener('click', () => {
        alert('سيتم توجيهك إلى صفحة إضافة التقييم بعد تسجيل الدخول.');
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
        // Tab switching functionality
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