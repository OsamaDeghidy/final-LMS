// Course Update Delete Functionality
document.addEventListener('DOMContentLoaded', function() {
    // Handle PDF delete checkboxes
    const deleteCheckboxes = document.querySelectorAll('.delete-checkbox');
    deleteCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const parentElement = this.closest('.d-flex') || this.closest('.list-group-item');
            if (parentElement) {
                if (this.checked) {
                    parentElement.classList.add('bg-danger', 'bg-opacity-10');
                } else {
                    parentElement.classList.remove('bg-danger', 'bg-opacity-10');
                }
            }
        });
    });

    // Handle module delete buttons
    const removeModuleBtns = document.querySelectorAll('.remove-module-btn');
    removeModuleBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const moduleId = this.getAttribute('data-module-id');
            if (moduleId) {
                const deleteInput = document.getElementById('delete_module_' + moduleId);
                if (deleteInput) {
                    deleteInput.value = '1';
                    const moduleCard = this.closest('.module-card');
                    if (moduleCard) {
                        moduleCard.classList.add('bg-danger', 'bg-opacity-10');
                        moduleCard.style.opacity = '0.7';
                        
                        // Add a restore button
                        const restoreBtn = document.createElement('button');
                        restoreBtn.type = 'button';
                        restoreBtn.className = 'btn btn-sm btn-success restore-module-btn ms-2';
                        restoreBtn.innerHTML = '<i class="fas fa-undo"></i>';
                        restoreBtn.setAttribute('data-module-id', moduleId);
                        
                        this.parentNode.insertBefore(restoreBtn, this.nextSibling);
                        this.style.display = 'none';
                        
                        // Add restore functionality
                        restoreBtn.addEventListener('click', function() {
                            deleteInput.value = '0';
                            moduleCard.classList.remove('bg-danger', 'bg-opacity-10');
                            moduleCard.style.opacity = '1';
                            this.previousSibling.style.display = 'inline-block';
                            this.remove();
                        });
                    }
                }
            }
        });
    });

    // Handle question delete buttons
    const removeQuestionBtns = document.querySelectorAll('.remove-question-btn');
    removeQuestionBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const questionId = this.getAttribute('data-question-id');
            if (questionId) {
                const deleteInput = document.getElementById('delete_question_' + questionId);
                if (deleteInput) {
                    deleteInput.value = '1';
                    const questionCard = this.closest('.question-card');
                    if (questionCard) {
                        questionCard.classList.add('bg-danger', 'bg-opacity-10');
                        questionCard.style.opacity = '0.7';
                        
                        // Add a restore button
                        const restoreBtn = document.createElement('button');
                        restoreBtn.type = 'button';
                        restoreBtn.className = 'btn btn-sm btn-success restore-question-btn ms-2';
                        restoreBtn.innerHTML = '<i class="fas fa-undo"></i>';
                        restoreBtn.setAttribute('data-question-id', questionId);
                        
                        this.parentNode.insertBefore(restoreBtn, this.nextSibling);
                        this.style.display = 'none';
                        
                        // Add restore functionality
                        restoreBtn.addEventListener('click', function() {
                            deleteInput.value = '0';
                            questionCard.classList.remove('bg-danger', 'bg-opacity-10');
                            questionCard.style.opacity = '1';
                            this.previousSibling.style.display = 'inline-block';
                            this.remove();
                        });
                    }
                }
            }
        });
    });

    // Handle answer delete buttons
    const removeAnswerBtns = document.querySelectorAll('.remove-answer-btn');
    removeAnswerBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const answerId = this.getAttribute('data-answer-id');
            if (answerId) {
                // If there's a hidden input for deletion, use it
                const deleteInput = document.getElementById('delete_answer_' + answerId);
                if (deleteInput) {
                    deleteInput.value = '1';
                    const answerItem = this.closest('.answer-item');
                    if (answerItem) {
                        answerItem.classList.add('bg-danger', 'bg-opacity-10');
                        answerItem.style.opacity = '0.7';
                        
                        // Add a restore button
                        const restoreBtn = document.createElement('button');
                        restoreBtn.type = 'button';
                        restoreBtn.className = 'btn btn-outline-success restore-answer-btn';
                        restoreBtn.innerHTML = '<i class="fas fa-undo"></i>';
                        restoreBtn.setAttribute('data-answer-id', answerId);
                        
                        this.parentNode.insertBefore(restoreBtn, this.nextSibling);
                        this.style.display = 'none';
                        
                        // Add restore functionality
                        restoreBtn.addEventListener('click', function() {
                            deleteInput.value = '0';
                            answerItem.classList.remove('bg-danger', 'bg-opacity-10');
                            answerItem.style.opacity = '1';
                            this.previousSibling.style.display = 'inline-block';
                            this.remove();
                        });
                    }
                } else {
                    // If no hidden input exists, just remove the answer (for newly added answers)
                    const answerItem = this.closest('.answer-item');
                    if (answerItem) {
                        answerItem.remove();
                    }
                }
            } else {
                // For newly added answers without IDs
                const answerItem = this.closest('.answer-item') || this.closest('.input-group');
                if (answerItem) {
                    answerItem.remove();
                }
            }
        });
    });

    // Fix quiz toggle functionality
    const quizToggles = document.querySelectorAll('.quiz-toggle');
    quizToggles.forEach(toggle => {
        toggle.addEventListener('change', function() {
            const moduleId = this.id.replace('has_quiz_existing_', '');
            const quizSection = document.getElementById('quiz_section_existing_' + moduleId);
            if (quizSection) {
                quizSection.style.display = this.checked ? 'block' : 'none';
            }
        });
    });
});
