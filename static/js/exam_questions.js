document.addEventListener('DOMContentLoaded', function() {
    // Question type toggle functionality
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
    
    // Add answer option functionality
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
    
    // Question reordering with drag and drop
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
                fetch(`/exam/${examId}/questions/reorder/`, {
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
    
    // Image preview functionality
    const questionImageInput = document.getElementById('image');
    const imagePreviewContainer = document.getElementById('image_preview_container');
    const imagePreview = document.getElementById('image_preview');
    
    if (questionImageInput && imagePreviewContainer && imagePreview) {
        questionImageInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    imagePreview.src = e.target.result;
                    imagePreviewContainer.style.display = 'block';
                };
                
                reader.readAsDataURL(this.files[0]);
            } else {
                imagePreviewContainer.style.display = 'none';
            }
        });
        
        // Clear image button
        const clearImageBtn = document.getElementById('clear_image');
        if (clearImageBtn) {
            clearImageBtn.addEventListener('click', function(e) {
                e.preventDefault();
                questionImageInput.value = '';
                imagePreviewContainer.style.display = 'none';
                
                // If there's a hidden input for marking image for deletion
                const deleteImageInput = document.getElementById('delete_image');
                if (deleteImageInput) {
                    deleteImageInput.value = 'true';
                }
            });
        }
    }
    
    // Points distribution helper
    const totalPointsDisplay = document.getElementById('total_points_display');
    const pointsInputs = document.querySelectorAll('.question-points-input');
    
    if (totalPointsDisplay && pointsInputs.length > 0) {
        function updateTotalPoints() {
            let total = 0;
            pointsInputs.forEach(input => {
                total += parseInt(input.value) || 0;
            });
            
            totalPointsDisplay.textContent = total;
            
            // Optional: Change color if total exceeds exam total points
            const examTotalPoints = parseInt(totalPointsDisplay.dataset.examTotal) || 100;
            if (total > examTotalPoints) {
                totalPointsDisplay.classList.add('text-danger');
            } else {
                totalPointsDisplay.classList.remove('text-danger');
            }
        }
        
        // Initial calculation
        updateTotalPoints();
        
        // Update on change
        pointsInputs.forEach(input => {
            input.addEventListener('change', updateTotalPoints);
            input.addEventListener('keyup', updateTotalPoints);
        });
    }
});
