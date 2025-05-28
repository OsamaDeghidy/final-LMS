// Course Update Delete Functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize event handlers
    initializeDeleteHandlers();
    initializeQuizToggles();
    initializeAddButtons();
    initializePdfDeleteButtons();
    
    // Add event listener to the "Submit" button
    const submitBtn = document.getElementById('submit-course-btn');
    if (submitBtn) {
        submitBtn.addEventListener('click', function(e) {
            e.preventDefault();
            submitCourse();
        });
    }
    
    // Function to initialize PDF delete buttons
    function initializePdfDeleteButtons() {
        // Initialize all delete buttons immediately
        const pdfDeleteButtons = document.querySelectorAll('.pdf-delete-btn');
        
        // Initialize buttons immediately
        pdfDeleteButtons.forEach(button => {
            button.addEventListener('click', async function() {
                const pdfType = this.getAttribute('data-pdf-type');
                if (!pdfType) return;

                // Get the course ID from the URL path (e.g., /123/update/)
                const match = window.location.pathname.match(/\/([\d]+)\/update\/$/);
                if (!match) {
                    console.error('Could not extract course ID from URL');
                    return;
                }
                const courseId = match[1];
                const pdfContainer = this.closest('.d-flex');
                const cardBody = pdfContainer.closest('.card-body');
                const deleteInput = cardBody.querySelector(`input[name="delete_${pdfType}"]`);

                if (!confirm('هل أنت متأكد من حذف هذا الملف؟')) {
                    return;
                }

                // Set the delete flag to 1
                if (deleteInput) {
                    deleteInput.value = '1';
                }

                // Show loading state
                const originalContent = pdfContainer.innerHTML;
                pdfContainer.innerHTML = `
                    <div class="d-flex align-items-center text-info">
                        <div class="spinner-border spinner-border-sm me-2" role="status">
                            <span class="visually-hidden">جاري التحميل...</span>
                        </div>
                        جاري حذف الملف...
                    </div>`;

                try {
                    const response = await fetch(`/delete-pdf/${courseId}/${pdfType}/`, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                            'Content-Type': 'application/x-www-form-urlencoded',
                        }
                    });

                    // Check if response is OK
                    if (!response.ok) {
                        throw new Error(`Server responded with status: ${response.status}`);
                    }
                    
                    // Try to parse as JSON, but handle non-JSON responses
                    let data;
                    const contentType = response.headers.get('content-type');
                    if (contentType && contentType.includes('application/json')) {
                        data = await response.json();
                    } else {
                        // If not JSON, consider it an error
                        throw new Error('Server did not return JSON response');
                    }

                    if (data.success) {
                        // File deleted successfully
                        const fileInput = cardBody.querySelector(`input[name="${pdfType}"]`);
                        if (fileInput) {
                            fileInput.value = ''; // Clear the file input
                        }
                        
                        // Show success message and remove the container after a delay
                        pdfContainer.innerHTML = `
                            <div class="alert alert-success mb-0 py-2">
                                <i class="fas fa-check-circle me-2"></i>تم حذف الملف بنجاح
                            </div>`;
                        
                        // Remove the container after 2 seconds
                        setTimeout(() => {
                            pdfContainer.remove();
                        }, 2000);
                    } else {
                        throw new Error(data.error || 'فشل حذف الملف');
                    }
                } catch (error) {
                    console.error('Error:', error);
                    pdfContainer.innerHTML = `
                        <div class="alert alert-danger mb-0 py-2">
                            <i class="fas fa-exclamation-circle me-2"></i>
                            ${error.message || 'حدث خطأ أثناء حذف الملف'}
                            <button type="button" class="btn-close float-end" data-bs-dismiss="alert"></button>
                        </div>`;
                    
                    // Restore original content after 3 seconds
                    setTimeout(() => {
                        pdfContainer.innerHTML = originalContent;
                        initializePdfDeleteButtons(); // Re-initialize the button
                    }, 3000);
                }
            });
        });
        
        // Add change event listeners to file inputs to handle file selection
        const pdfFileInputs = document.querySelectorAll('input[type="file"][accept="application/pdf"]');
        pdfFileInputs.forEach(input => {
            input.addEventListener('change', function() {
                const pdfType = this.name; // syllabus_pdf or materials_pdf
                if (this.files.length > 0) {
                    // If a new file is selected, make sure the delete flag is reset
                    const deleteInput = document.getElementById('delete_' + pdfType);
                    if (deleteInput) {
                        deleteInput.value = '0';
                    }
                    
                    // If there was a deletion message, remove it
                    const warningMsg = this.parentNode.querySelector('.alert-warning');
                    if (warningMsg) {
                        warningMsg.remove();
                    }
                }
            });
        });
    }

    // Function to initialize all delete handlers
    function initializeDeleteHandlers() {
        // Handle PDF delete checkboxes
        const deleteCheckboxes = document.querySelectorAll('.delete-checkbox');
        deleteCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                const parentElement = this.closest('.d-flex') || this.closest('.list-group-item');
                if (parentElement) {
                    if (this.checked) {
                        parentElement.classList.add('bg-danger', 'bg-opacity-10');
                        // Ensure the checkbox value is set to 1 when checked
                        this.value = '1';
                    } else {
                        parentElement.classList.remove('bg-danger', 'bg-opacity-10');
                        // Reset the checkbox value to 0 when unchecked
                        this.value = '0';
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

        // Handle video name remove buttons
        document.querySelectorAll('.remove-video-name-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const videoNameItem = this.closest('.input-group');
                if (videoNameItem) {
                    videoNameItem.remove();
                }
            });
        });

        // Handle note remove buttons
        document.querySelectorAll('.remove-note-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const noteItem = this.closest('.input-group');
                if (noteItem) {
                    noteItem.remove();
                }
            });
        });
    }

    // Function to initialize quiz toggles
    function initializeQuizToggles() {
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
    }

    // Function to initialize add buttons
    function initializeAddButtons() {
        // Add module button
        const addModuleBtn = document.getElementById('add-module-btn');
        if (addModuleBtn) {
            addModuleBtn.addEventListener('click', addNewModule);
        }

        // Add question buttons
        document.querySelectorAll('.add-question-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const moduleId = this.getAttribute('data-module-id');
                addNewQuestion(moduleId);
            });
        });

        // Add answer buttons
        document.querySelectorAll('.add-answer-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const questionCard = this.closest('.question-card');
                if (questionCard) {
                    const answersContainer = questionCard.querySelector('.answers-container');
                    if (answersContainer) {
                        // Extract moduleId and questionId from the container ID
                        const containerId = answersContainer.id;
                        let moduleId, questionId;
                        const match = containerId.match(/answers_(?:existing_question_|new_)?(\d+)(?:_(\d+))?/);
                        if (match) {
                            moduleId = match[1];
                            questionId = match[2] || '';
                        }
                        addNewAnswer(answersContainer, moduleId, questionId);
                    }
                }
            });
        });

        // Add note buttons
        document.querySelectorAll('.add-note-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const moduleId = this.getAttribute('data-module-id');
                addNewNote(moduleId);
            });
        });

        // Add video name buttons
        document.querySelectorAll('.add-video-name-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const moduleId = this.getAttribute('data-module-id');
                addNewVideoName(moduleId);
            });
        });
    }
});

// Function to add a new module
function addNewModule() {
    const modulesContainer = document.getElementById('modules-container');
    if (!modulesContainer) return;
    
    // Get the current number of modules (including deleted ones)
    const moduleCount = modulesContainer.querySelectorAll('.module-card').length;
    const newModuleNumber = moduleCount + 1;
    const newModuleId = 'new_' + Date.now(); // Use timestamp for unique ID
    
    const moduleHtml = `
    <div class="card mb-4 module-card" id="module_${newModuleId}">
        <div class="card-header bg-light d-flex justify-content-between align-items-center">
            <h5 class="mb-0"><i class="fas fa-layer-group text-primary me-2"></i>الموديول ${newModuleNumber}</h5>
            <button type="button" class="btn btn-sm btn-outline-danger remove-module-btn" data-module-id="${newModuleId}">
                <i class="fas fa-trash"></i>
            </button>
            <input type="hidden" name="delete_module_${newModuleId}" id="delete_module_${newModuleId}" value="0">
        </div>
        <div class="card-body">
            <!-- Module Info -->
            <div class="mb-3">
                <label class="form-label fw-bold">اسم الموديول</label>
                <input type="text" class="form-control" name="module_name_new_${newModuleId}" placeholder="أدخل اسم الموديول" required>
                <input type="hidden" name="module_id_new_${newModuleId}" value="new">
            </div>
            
            <!-- Videos -->
            <div class="mb-3">
                <label class="form-label fw-bold">إضافة فيديوهات جديدة</label>
                <input type="file" class="form-control" name="module_videos_new_${newModuleId}" accept="video/*" multiple>
                <small class="text-muted">الصيغ المدعومة: MP4, MOV, AVI</small>
            </div>
            
            <!-- Notes -->
            <div class="mb-3">
                <label class="form-label fw-bold">ملاحظات إضافية</label>
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <div></div>
                    <button type="button" class="btn btn-sm btn-outline-primary add-note-btn" data-module-id="${newModuleId}">
                        <i class="fas fa-plus me-1"></i>إضافة ملاحظة
                    </button>
                </div>
                <div class="notes-container" id="notes_container_${newModuleId}">
                    <div class="input-group mb-2">
                        <textarea class="form-control" name="module_notes_new_${newModuleId}_0" rows="2" placeholder="أدخل ملاحظة"></textarea>
                        <button type="button" class="btn btn-outline-danger remove-note-btn">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
            </div>
            
            <!-- Video Names -->
            <div class="mb-3">
                <label class="form-label fw-bold">عناوين الفيديوهات الجديدة</label>
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <div></div>
                    <button type="button" class="btn btn-sm btn-outline-primary add-video-name-btn" data-module-id="${newModuleId}">
                        <i class="fas fa-plus me-1"></i>إضافة عنوان
                    </button>
                </div>
                <div class="video-names-container" id="video_names_container_${newModuleId}">
                    <div class="input-group mb-2">
                        <span class="input-group-text bg-light"><i class="fas fa-video text-primary"></i></span>
                        <input type="text" class="form-control" name="video_name_new_${newModuleId}_0" placeholder="أدخل عنوان الفيديو">
                        <button type="button" class="btn btn-outline-danger remove-video-name-btn">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
            </div>
            
            <!-- Quiz Section -->
            <div class="card mb-3 border-primary">
                <div class="card-header bg-light">
                    <div class="form-check form-switch">
                        <input class="form-check-input quiz-toggle" type="checkbox" id="has_quiz_new_${newModuleId}" name="has_quiz_new_${newModuleId}">
                        <label class="form-check-label fw-bold" for="has_quiz_new_${newModuleId}">إضافة اختبار للموديول</label>
                    </div>
                </div>
                <div class="quiz-section card-body" id="quiz_section_new_${newModuleId}" style="display: none;">
                    <div class="mb-3">
                        <label class="form-label fw-bold">عنوان الاختبار</label>
                        <input type="text" class="form-control" name="quiz_title_new_${newModuleId}" placeholder="أدخل عنوان الاختبار">
                    </div>
                    <div class="mb-3">
                        <label class="form-label fw-bold">وصف الاختبار</label>
                        <textarea class="form-control" name="quiz_description_new_${newModuleId}" rows="2" placeholder="وصف مختصر للاختبار"></textarea>
                    </div>
                    <div class="row mb-3">
                        <div class="col-md-6">
                            <label class="form-label fw-bold">درجة النجاح (%)</label>
                            <input type="number" class="form-control" name="quiz_pass_mark_new_${newModuleId}" min="0" max="100" value="50">
                        </div>
                        <div class="col-md-6">
                            <label class="form-label fw-bold">مدة الاختبار (دقائق)</label>
                            <input type="number" class="form-control" name="quiz_time_limit_new_${newModuleId}" min="1" value="10">
                        </div>
                    </div>
                    
                    <div class="questions-container" id="questions_container_new_${newModuleId}">
                        <!-- Questions will be added here -->
                    </div>
                    
                    <button type="button" class="btn btn-primary w-100 mt-3 add-question-btn" data-module-id="new_${newModuleId}">
                        <i class="fas fa-plus me-1"></i>إضافة سؤال جديد
                    </button>
                </div>
            </div>
        </div>
    </div>
    `;
    
    modulesContainer.insertAdjacentHTML('beforeend', moduleHtml);
    
    // Add event listeners to the new elements
    const newModule = document.getElementById(`module_${newModuleId}`);
    if (newModule) {
        // Add event listener to remove module button
        const removeBtn = newModule.querySelector('.remove-module-btn');
        if (removeBtn) {
            removeBtn.addEventListener('click', function() {
                newModule.remove();
            });
        }
        
        // Add event listener to quiz toggle
        const quizToggle = newModule.querySelector('.quiz-toggle');
        if (quizToggle) {
            quizToggle.addEventListener('change', function() {
                const quizSection = document.getElementById(`quiz_section_new_${newModuleId}`);
                if (quizSection) {
                    quizSection.style.display = this.checked ? 'block' : 'none';
                }
            });
        }
        
        // Add event listeners to add buttons
        const addNoteBtn = newModule.querySelector('.add-note-btn');
        if (addNoteBtn) {
            addNoteBtn.addEventListener('click', function() {
                addNewNote(`new_${newModuleId}`);
            });
        }
        
        const addVideoNameBtn = newModule.querySelector('.add-video-name-btn');
        if (addVideoNameBtn) {
            addVideoNameBtn.addEventListener('click', function() {
                addNewVideoName(`new_${newModuleId}`);
            });
        }
        
        const addQuestionBtn = newModule.querySelector('.add-question-btn');
        if (addQuestionBtn) {
            addQuestionBtn.addEventListener('click', function() {
                addNewQuestion(`new_${newModuleId}`);
            });
        }
        
        // Add event listeners to remove buttons
        newModule.querySelectorAll('.remove-note-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const noteItem = this.closest('.input-group');
                if (noteItem) {
                    noteItem.remove();
                }
            });
        });
        
        newModule.querySelectorAll('.remove-video-name-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const videoNameItem = this.closest('.input-group');
                if (videoNameItem) {
                    videoNameItem.remove();
                }
            });
        });
    }
}

// Function to add a new question
function addNewQuestion(moduleId) {
    const questionsContainer = document.getElementById(`questions_container_${moduleId}`);
    if (!questionsContainer) return;
    
    // Get the current number of questions
    const questionCount = questionsContainer.querySelectorAll('.question-card').length;
    const newQuestionNumber = questionCount + 1;
    const timestamp = Date.now();
    
    const questionHtml = `
    <div class="card mb-3 question-card" id="question_${moduleId}_${timestamp}">
        <div class="card-body">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h6 class="mb-0">سؤال #${newQuestionNumber}</h6>
                <button type="button" class="btn btn-sm btn-outline-danger remove-question-btn">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            
            <div class="mb-3">
                <input type="text" class="form-control" name="question_text_${moduleId}_${timestamp}" placeholder="نص السؤال" required>
            </div>
            
            <div class="mb-3">
                <select class="form-select question-type-select" name="question_type_${moduleId}_${timestamp}">
                    <option value="multiple_choice">اختيار من متعدد</option>
                    <option value="true_false">صح أو خطأ</option>
                    <option value="short_answer">إجابة قصيرة</option>
                </select>
            </div>
            
            <div class="answers-container" id="answers_${moduleId}_${timestamp}">
                <!-- Multiple Choice Answers -->
                <div class="answer-item mb-2">
                    <div class="input-group">
                        <div class="input-group-text">
                            <input class="form-check-input mt-0" type="radio" name="correct_answer_${moduleId}_${timestamp}" value="0" checked>
                        </div>
                        <input type="text" class="form-control" name="answer_text_${moduleId}_${timestamp}_0" placeholder="الإجابة 1" required>
                        <button type="button" class="btn btn-outline-danger remove-answer-btn">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
            </div>
            
            <button type="button" class="btn btn-sm btn-outline-primary mt-2 add-answer-btn">
                <i class="fas fa-plus me-1"></i>إضافة إجابة
            </button>
        </div>
    </div>
    `;
    
    questionsContainer.insertAdjacentHTML('beforeend', questionHtml);
    
    // Add event listeners to the new elements
    const newQuestion = document.getElementById(`question_${moduleId}_${timestamp}`);
    if (newQuestion) {
        // Add event listener to remove question button
        const removeBtn = newQuestion.querySelector('.remove-question-btn');
        if (removeBtn) {
            removeBtn.addEventListener('click', function() {
                newQuestion.remove();
            });
        }
        
        // Add event listener to question type select
        const typeSelect = newQuestion.querySelector('.question-type-select');
        if (typeSelect) {
            typeSelect.addEventListener('change', function() {
                const answersContainer = document.getElementById(`answers_${moduleId}_${timestamp}`);
                if (answersContainer) {
                    // Clear existing answers
                    answersContainer.innerHTML = '';
                    
                    // Add appropriate answers based on question type
                    if (this.value === 'multiple_choice') {
                        // Add a single multiple choice answer
                        const answerHtml = `
                        <div class="answer-item mb-2">
                            <div class="input-group">
                                <div class="input-group-text">
                                    <input class="form-check-input mt-0" type="radio" name="correct_answer_${moduleId}_${timestamp}" value="0" checked>
                                </div>
                                <input type="text" class="form-control" name="answer_text_${moduleId}_${timestamp}_0" placeholder="الإجابة 1" required>
                                <button type="button" class="btn btn-outline-danger remove-answer-btn">
                                    <i class="fas fa-times"></i>
                                </button>
                            </div>
                        </div>
                        `;
                        answersContainer.insertAdjacentHTML('beforeend', answerHtml);
                        
                        // Show add answer button
                        const addAnswerBtn = newQuestion.querySelector('.add-answer-btn');
                        if (addAnswerBtn) {
                            addAnswerBtn.style.display = 'inline-block';
                        }
                    } else if (this.value === 'true_false') {
                        // Add true/false answers
                        const answersHtml = `
                        <div class="answer-item mb-2">
                            <div class="input-group">
                                <div class="input-group-text">
                                    <input class="form-check-input mt-0" type="radio" name="correct_answer_${moduleId}_${timestamp}" value="0" checked>
                                </div>
                                <input type="text" class="form-control" name="answer_text_${moduleId}_${timestamp}_0" value="صح" readonly>
                            </div>
                        </div>
                        <div class="answer-item mb-2">
                            <div class="input-group">
                                <div class="input-group-text">
                                    <input class="form-check-input mt-0" type="radio" name="correct_answer_${moduleId}_${timestamp}" value="1">
                                </div>
                                <input type="text" class="form-control" name="answer_text_${moduleId}_${timestamp}_1" value="خطأ" readonly>
                            </div>
                        </div>
                        `;
                        answersContainer.insertAdjacentHTML('beforeend', answersHtml);
                        
                        // Hide add answer button
                        const addAnswerBtn = newQuestion.querySelector('.add-answer-btn');
                        if (addAnswerBtn) {
                            addAnswerBtn.style.display = 'none';
                        }
                    } else if (this.value === 'short_answer') {
                        // Add short answer input
                        const answerHtml = `
                        <div class="mb-3">
                            <label class="form-label">الإجابة الصحيحة</label>
                            <input type="text" class="form-control" name="answer_short_${moduleId}_${timestamp}" placeholder="أدخل الإجابة الصحيحة" required>
                        </div>
                        `;
                        answersContainer.insertAdjacentHTML('beforeend', answerHtml);
                        
                        // Hide add answer button
                        const addAnswerBtn = newQuestion.querySelector('.add-answer-btn');
                        if (addAnswerBtn) {
                            addAnswerBtn.style.display = 'none';
                        }
                    }
                    
                    // Add event listeners to new remove answer buttons
                    const removeAnswerBtns = answersContainer.querySelectorAll('.remove-answer-btn');
                    removeAnswerBtns.forEach(btn => {
                        btn.addEventListener('click', function() {
                            const answerItem = this.closest('.answer-item');
                            if (answerItem) {
                                answerItem.remove();
                            }
                        });
                    });
                }
            });
        }
        
        // Add event listener to add answer button
        const addAnswerBtn = newQuestion.querySelector('.add-answer-btn');
        if (addAnswerBtn) {
            addAnswerBtn.addEventListener('click', function() {
                const answersContainer = document.getElementById(`answers_${moduleId}_${timestamp}`);
                if (answersContainer) {
                    addNewAnswer(answersContainer, moduleId, timestamp);
                }
            });
        }
        
        // Add event listeners to remove answer buttons
        const removeAnswerBtns = newQuestion.querySelectorAll('.remove-answer-btn');
        removeAnswerBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const answerItem = this.closest('.answer-item');
                if (answerItem) {
                    answerItem.remove();
                }
            });
        });
    }
}

// Function to add a new answer to a question
function addNewAnswer(answersContainer, moduleId, questionId) {
    if (!answersContainer) return;
    
    // Get the current number of answers
    const answerCount = answersContainer.querySelectorAll('.answer-item').length;
    const newAnswerNumber = answerCount;
    
    // Extract moduleId and questionId from the container ID if not provided
    if (!moduleId || !questionId) {
        const containerId = answersContainer.id;
        const match = containerId.match(/answers_(?:existing_question_|new_)?(\d+)(?:_(\d+))?/);
        if (match) {
            moduleId = moduleId || match[1];
            questionId = questionId || match[2] || '';
        }
    }
    
    // Create the answer HTML
    const answerHtml = `
    <div class="answer-item mb-2">
        <div class="input-group">
            <div class="input-group-text">
                <input class="form-check-input mt-0" type="radio" name="correct_answer_${moduleId}_${questionId}" value="${newAnswerNumber}">
            </div>
            <input type="text" class="form-control" name="answer_text_${moduleId}_${questionId}_${newAnswerNumber}" placeholder="الإجابة ${newAnswerNumber + 1}" required>
            <button type="button" class="btn btn-outline-danger remove-answer-btn">
                <i class="fas fa-times"></i>
            </button>
        </div>
    </div>
    `;
    
    answersContainer.insertAdjacentHTML('beforeend', answerHtml);
    
    // Add event listener to the new remove button
    const newAnswer = answersContainer.lastElementChild;
    if (newAnswer) {
        const removeBtn = newAnswer.querySelector('.remove-answer-btn');
        if (removeBtn) {
            removeBtn.addEventListener('click', function() {
                newAnswer.remove();
            });
        }
    }
}

// Function to add a new note
function addNewNote(moduleId) {
    const notesContainer = document.getElementById(`notes_container_${moduleId}`);
    if (!notesContainer) return;
    
    // Get the current number of notes
    const noteCount = notesContainer.querySelectorAll('.input-group').length;
    
    const noteHtml = `
    <div class="input-group mb-2">
        <textarea class="form-control" name="module_notes_${moduleId}_${noteCount}" rows="2" placeholder="أدخل ملاحظة"></textarea>
        <button type="button" class="btn btn-outline-danger remove-note-btn">
            <i class="fas fa-times"></i>
        </button>
    </div>
    `;
    
    notesContainer.insertAdjacentHTML('beforeend', noteHtml);
    
    // Add event listener to the new remove button
    const newNote = notesContainer.lastElementChild;
    if (newNote) {
        const removeBtn = newNote.querySelector('.remove-note-btn');
        if (removeBtn) {
            removeBtn.addEventListener('click', function() {
                newNote.remove();
            });
        }
    }
}

// Function to add a new video name
function addNewVideoName(moduleId) {
    const videoNamesContainer = document.getElementById(`video_names_container_${moduleId}`);
    if (!videoNamesContainer) return;
    
    // Get the current number of video names
    const videoNameCount = videoNamesContainer.querySelectorAll('.input-group').length;
    
    const videoNameHtml = `
    <div class="input-group mb-2">
        <span class="input-group-text bg-light"><i class="fas fa-video text-primary"></i></span>
        <input type="text" class="form-control" name="video_name_${moduleId}_${videoNameCount}" placeholder="أدخل عنوان الفيديو">
        <button type="button" class="btn btn-outline-danger remove-video-name-btn">
            <i class="fas fa-times"></i>
        </button>
    </div>
    `;
    
    videoNamesContainer.insertAdjacentHTML('beforeend', videoNameHtml);
    
    // Add event listener to the new remove button
    const newVideoName = videoNamesContainer.lastElementChild;
    if (newVideoName) {
        const removeBtn = newVideoName.querySelector('.remove-video-name-btn');
        if (removeBtn) {
            removeBtn.addEventListener('click', function() {
                newVideoName.remove();
            });
        }
    }
}

// Submit the course form
function submitCourse() {
    if (validateForm()) {
        // Check if any PDF is marked for deletion and handle file inputs accordingly
        const pdfTypes = ['syllabus_pdf', 'materials_pdf'];
        pdfTypes.forEach(pdfType => {
            const deleteInput = document.getElementById('delete_' + pdfType);
            const fileInput = document.querySelector(`input[name="${pdfType}"]`);
            
            // If marked for deletion and no new file is selected, ensure we keep the delete flag
            if (deleteInput && deleteInput.value === '1' && fileInput && fileInput.files.length === 0) {
                // The delete flag is already set, no need to do anything
            } 
            // If a new file is selected, make sure the delete flag is reset
            else if (fileInput && fileInput.files.length > 0 && deleteInput) {
                deleteInput.value = '0';
            }
        });
        
        document.getElementById('course-form').submit();
    }
}

// Validate the form before submission
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
