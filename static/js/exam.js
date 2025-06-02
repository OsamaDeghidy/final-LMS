document.addEventListener('DOMContentLoaded', function() {
    // Exam timer functionality
    const timerElement = document.getElementById('exam-timer');
    const timerForm = document.getElementById('timer-form');
    const examForm = document.getElementById('exam-form');
    
    if (timerElement) {
        let timeLeft = parseInt(timerElement.dataset.timeLeft);
        const examId = timerElement.dataset.examId;
        const attemptId = timerElement.dataset.attemptId;
        
        // Update timer every second
        const timerInterval = setInterval(function() {
            if (timeLeft <= 0) {
                clearInterval(timerInterval);
                // Auto-submit the form when time is up
                if (timerForm) {
                    timerForm.submit();
                }
                return;
            }
            
            timeLeft -= 1;
            
            // Format time as HH:MM:SS
            const hours = Math.floor(timeLeft / 3600);
            const minutes = Math.floor((timeLeft % 3600) / 60);
            const seconds = timeLeft % 60;
            
            const formattedTime = 
                String(hours).padStart(2, '0') + ':' +
                String(minutes).padStart(2, '0') + ':' +
                String(seconds).padStart(2, '0');
            
            timerElement.textContent = formattedTime;
            
            // Add warning class when less than 5 minutes remaining
            if (timeLeft <= 300) {
                timerElement.classList.add('timer-warning');
            }
        }, 1000);
    }
    
    // Auto-save functionality for exam answers
    const autoSaveForm = document.getElementById('exam-form');
    if (autoSaveForm) {
        const attemptId = autoSaveForm.dataset.attemptId;
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        // Auto-save every 30 seconds
        setInterval(function() {
            const formData = new FormData(autoSaveForm);
            
            fetch('/exams/autosave/' + attemptId + '/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const saveStatus = document.getElementById('save-status');
                    if (saveStatus) {
                        saveStatus.textContent = 'تم الحفظ التلقائي ' + new Date().toLocaleTimeString();
                        saveStatus.classList.add('show');
                        
                        // Hide the status after 3 seconds
                        setTimeout(() => {
                            saveStatus.classList.remove('show');
                        }, 3000);
                    }
                }
            })
            .catch(error => console.error('Error auto-saving:', error));
        }, 30000);
    }
    
    // Confirm before leaving the exam page
    if (examForm) {
        window.addEventListener('beforeunload', function(e) {
            // Cancel the event
            e.preventDefault();
            // Chrome requires returnValue to be set
            e.returnValue = '';
        });
        
        // Don't show the warning when submitting the form
        examForm.addEventListener('submit', function() {
            window.removeEventListener('beforeunload', function() {});
        });
    }
    
    // Question type toggle in add/edit question forms
    const questionTypeSelect = document.getElementById('question_type');
    if (questionTypeSelect) {
        const multipleChoiceSection = document.getElementById('multiple_choice_section');
        const trueFalseSection = document.getElementById('true_false_section');
        const shortAnswerSection = document.getElementById('short_answer_section');
        
        function toggleQuestionSections() {
            const selectedType = questionTypeSelect.value;
            
            if (multipleChoiceSection) {
                multipleChoiceSection.style.display = selectedType === 'multiple_choice' ? 'block' : 'none';
            }
            
            if (trueFalseSection) {
                trueFalseSection.style.display = selectedType === 'true_false' ? 'block' : 'none';
            }
            
            if (shortAnswerSection) {
                shortAnswerSection.style.display = selectedType === 'short_answer' ? 'block' : 'none';
            }
        }
        
        // Initial toggle
        toggleQuestionSections();
        
        // Toggle on change
        questionTypeSelect.addEventListener('change', toggleQuestionSections);
    }
    
    // Add/remove answer options in multiple choice questions
    const addAnswerBtn = document.getElementById('add_answer_option');
    if (addAnswerBtn) {
        const answerContainer = document.getElementById('answer_options_container');
        
        addAnswerBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            const answerCount = answerContainer.querySelectorAll('.answer-option').length;
            const newAnswerId = answerCount + 1;
            
            const answerTemplate = `
                <div class="answer-option mb-3 border rounded p-3 position-relative">
                    <button type="button" class="btn btn-sm btn-outline-danger remove-answer position-absolute top-0 end-0 m-2">
                        <i class="fas fa-times"></i>
                    </button>
                    <div class="mb-3">
                        <label for="answer_text_${newAnswerId}" class="form-label">نص الإجابة</label>
                        <input type="text" class="form-control" id="answer_text_${newAnswerId}" name="answer_text[]" required>
                    </div>
                    <div class="form-check">
                        <input class="form-check-input" type="radio" name="is_correct" id="is_correct_${newAnswerId}" value="${newAnswerId-1}">
                        <label class="form-check-label" for="is_correct_${newAnswerId}">
                            إجابة صحيحة
                        </label>
                    </div>
                </div>
            `;
            
            answerContainer.insertAdjacentHTML('beforeend', answerTemplate);
            
            // Add event listeners to new remove buttons
            const removeButtons = answerContainer.querySelectorAll('.remove-answer');
            removeButtons.forEach(button => {
                button.addEventListener('click', function() {
                    this.closest('.answer-option').remove();
                });
            });
        });
        
        // Initial remove button functionality
        const removeButtons = document.querySelectorAll('.remove-answer');
        removeButtons.forEach(button => {
            button.addEventListener('click', function() {
                this.closest('.answer-option').remove();
            });
        });
    }
    
    // Initialize Sortable for question reordering
    const questionsList = document.getElementById('questions-list');
    if (questionsList && typeof Sortable !== 'undefined') {
        new Sortable(questionsList, {
            animation: 150,
            ghostClass: 'bg-light',
            handle: '.drag-handle',
            onEnd: function(evt) {
                const examId = questionsList.dataset.examId;
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
                
                // Get the new order of questions
                const questionIds = Array.from(questionsList.querySelectorAll('.question-item'))
                    .map(item => item.dataset.questionId);
                
                // Send the new order to the server
                fetch(`/exams/reorder-questions/${examId}/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify({
                        question_ids: questionIds
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Show success message
                        const alert = document.createElement('div');
                        alert.className = 'alert alert-success alert-dismissible fade show';
                        alert.innerHTML = `
                            تم حفظ ترتيب الأسئلة بنجاح
                            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                        `;
                        
                        const alertContainer = document.getElementById('alert-container');
                        if (alertContainer) {
                            alertContainer.appendChild(alert);
                            
                            // Auto-dismiss after 3 seconds
                            setTimeout(() => {
                                alert.classList.remove('show');
                                setTimeout(() => {
                                    alert.remove();
                                }, 150);
                            }, 3000);
                        }
                    }
                })
                .catch(error => console.error('Error updating question order:', error));
            }
        });
    }
});
