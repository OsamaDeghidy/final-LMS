// Course Update Delete Functionality
// Function to handle PDF file removal
function handlePdfRemoval(pdfId) {
  if (confirm('هل أنت متأكد من حذف هذا الملف؟')) {
    fetch(`/courses/remove-pdf/${pdfId}/`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
        'X-Requested-With': 'XMLHttpRequest'
      }
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        // Remove the PDF element from the UI
        const pdfElement = document.querySelector(`[data-pdf-id="${pdfId}"]`).closest('.list-group-item');
        pdfElement.remove();
        showAlert('success', data.message);
      } else {
        showAlert('danger', data.message || 'حدث خطأ أثناء حذف الملف');
      }
    })
    .catch(error => {
      console.error('Error:', error);
      showAlert('danger', 'حدث خطأ في الشبكة');
    });
  }
}

// Function to initialize add buttons for notes, video names, and questions
function initializeAddButtons() {
  // Add note buttons
  document.addEventListener('click', function(e) {
    if (e.target.closest('.add-note-btn')) {
      const btn = e.target.closest('.add-note-btn');
      const moduleId = btn.getAttribute('data-module-id');
      if (moduleId) {
        addNewNote(moduleId);
      }
    }
  });

  // Add video name buttons
  document.addEventListener('click', function(e) {
    if (e.target.closest('.add-video-name-btn')) {
      const btn = e.target.closest('.add-video-name-btn');
      const moduleId = btn.getAttribute('data-module-id');
      if (moduleId) {
        addNewVideoName(moduleId);
      }
    }
  });

  // Add question buttons
  document.addEventListener('click', function(e) {
    if (e.target.closest('.add-question-btn')) {
      const btn = e.target.closest('.add-question-btn');
      const moduleId = btn.getAttribute('data-module-id');
      if (moduleId) {
        addNewQuestion(moduleId);
      }
    }
  });
}

// Function to initialize the application
function initializeApp() {
  // Add event listeners for PDF removal buttons
  document.querySelectorAll('.remove-pdf-btn').forEach(btn => {
    btn.addEventListener('click', function() {
      const pdfId = this.getAttribute('data-pdf-id');
      handlePdfRemoval(pdfId);
    });
  });

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

  // Add event listener to #add-module-btn to call addNewModule()
  document.getElementById('add-module-btn')?.addEventListener('click', addNewModule);
}

// Initialize the app when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', initializeApp);

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
                const match = window.location.pathname.match(/\/(\d+)\/update\//);
                if (!match) {
                    console.error('Could not extract course ID from URL');
                    return;
                }
                const courseId = match[1];
                const pdfContainer = this.closest('.d-flex');
                const cardBody = pdfContainer.closest('.card-body');
                
                // Create hidden input for delete flag if it doesn't exist
                let deleteInput = document.getElementById(`delete_${pdfType}`);
                if (!deleteInput) {
                    deleteInput = document.createElement('input');
                    deleteInput.type = 'hidden';
                    deleteInput.name = `delete_${pdfType}`;
                    deleteInput.id = `delete_${pdfType}`;
                    deleteInput.value = '0';
                    cardBody.appendChild(deleteInput);
                }

                if (!confirm('هل أنت متأكد من حذف هذا الملف؟')) {
                    return;
                }

                // Set the delete flag to 1
                deleteInput.value = '1';

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
                        // Get the parent column div that contains the label and file input
                        const parentColumn = pdfContainer.closest('.col-md-6.mb-3');
                        if (!parentColumn) {
                            throw new Error('Could not find parent column');
                        }
                        
                        // Keep the label
                        const label = parentColumn.querySelector('.form-label');
                        const labelHtml = label ? label.outerHTML : '';
                        
                        // Create new content with file input and success message
                        parentColumn.innerHTML = `
                            ${labelHtml}
                            <div class="alert alert-success mb-2">
                                <i class="fas fa-check-circle me-2"></i>تم حذف الملف بنجاح
                            </div>
                            <input type="file" class="form-control" name="${pdfType}" accept="application/pdf">
                            <small class="text-muted">اختياري. حجم الملف الأقصى: 10 ميجابايت</small>
                            <input type="hidden" name="delete_${pdfType}" id="delete_${pdfType}" value="1">
                        `;
                        
                        // Add change event listener to the new file input
                        const newFileInput = parentColumn.querySelector(`input[name="${pdfType}"]`);
                        if (newFileInput) {
                            newFileInput.addEventListener('change', function() {
                                if (this.files.length > 0) {
                                    // If a new file is selected, reset the delete flag
                                    const deleteInput = document.getElementById(`delete_${pdfType}`);
                                    if (deleteInput) {
                                        deleteInput.value = '0';
                                    }
                                    
                                    // Remove success message if it exists
                                    const successMsg = parentColumn.querySelector('.alert-success');
                                    if (successMsg) {
                                        successMsg.remove();
                                    }
                                }
                            });
                        }
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
                    
                    // If there was a success message, remove it
                    const successMsg = this.parentNode.querySelector('.alert-success');
                    if (successMsg) {
                        successMsg.remove();
                    }
                    
                    // Validate file size
                    const maxSize = 10 * 1024 * 1024; // 10MB
                    if (this.files[0].size > maxSize) {
                        // Show error message
                        const errorDiv = document.createElement('div');
                        errorDiv.className = 'alert alert-danger mt-2';
                        errorDiv.innerHTML = '<i class="fas fa-exclamation-circle me-2"></i>حجم الملف كبير جدًا. الحد الأقصى هو 10 ميجابايت.';
                        this.parentNode.insertBefore(errorDiv, this.nextSibling);
                        
                        // Clear the file input
                        this.value = '';
                    } else {
                        // Show file selected message
                        const fileInfoDiv = document.createElement('div');
                        fileInfoDiv.className = 'alert alert-info mt-2';
                        fileInfoDiv.innerHTML = `<i class="fas fa-file-pdf me-2"></i>تم اختيار: ${this.files[0].name}`;
                        this.parentNode.insertBefore(fileInfoDiv, this.nextSibling);
                    }
                }
            });
        });
    }

    // Function to initialize all delete handlers
    function initializeDeleteHandlers() {
        // Handle PDF delete checkboxes using event delegation
        document.addEventListener('change', function(e) {
            if (e.target.classList.contains('delete-checkbox')) {
                const checkbox = e.target;
                const parentElement = checkbox.closest('.d-flex') || checkbox.closest('.list-group-item');
                if (parentElement) {
                    const isChecked = checkbox.checked;
                    parentElement.classList.toggle('bg-danger', isChecked);
                    parentElement.classList.toggle('bg-opacity-10', isChecked);
                    checkbox.value = isChecked ? '1' : '0';
                    
                    const deleteInput = document.getElementById(checkbox.getAttribute('data-delete-input'));
                    if (deleteInput) {
                        deleteInput.value = isChecked ? '1' : '0';
                    }
                }
            }
        });

        // Handle file input changes using event delegation
        document.addEventListener('change', function(e) {
            if (e.target.type === 'file' && e.target.files.length > 0) {
                const input = e.target;
                // Clear any deletion flags when new file is selected
                const deleteInput = document.getElementById(input.getAttribute('data-delete-input'));
                if (deleteInput) {
                    deleteInput.value = '0';
                }
                // Show file name
                const fileNameDisplay = input.nextElementSibling;
                if (fileNameDisplay) {
                    fileNameDisplay.textContent = input.files[0].name;
                }
            }
        });


        // Handle module delete and restore buttons using event delegation
        document.addEventListener('click', function(e) {
            // Handle delete button clicks
            if (e.target.closest('.remove-module-btn')) {
                const btn = e.target.closest('.remove-module-btn');
                const moduleId = btn.getAttribute('data-module-id');
                if (moduleId) {
                    const deleteInput = document.getElementById('delete_module_' + moduleId);
                    if (deleteInput) {
                        deleteInput.value = '1';
                        const moduleCard = btn.closest('.module-card');
                        if (moduleCard) {
                            moduleCard.classList.add('bg-danger', 'bg-opacity-10');
                            moduleCard.style.opacity = '0.7';
                            
                            // Add a restore button
                            const restoreBtn = document.createElement('button');
                            restoreBtn.type = 'button';
                            restoreBtn.className = 'btn btn-sm btn-success restore-module-btn ms-2';
                            restoreBtn.innerHTML = '<i class="fas fa-undo"></i>';
                            restoreBtn.setAttribute('data-module-id', moduleId);
                            
                            btn.parentNode.insertBefore(restoreBtn, btn.nextSibling);
                            btn.style.display = 'none';
                        }
                    }
                }
            }
            // Handle restore button clicks
            else if (e.target.closest('.restore-module-btn')) {
                const restoreBtn = e.target.closest('.restore-module-btn');
                const moduleId = restoreBtn.getAttribute('data-module-id');
                if (moduleId) {
                    const deleteInput = document.getElementById('delete_module_' + moduleId);
                    const moduleCard = restoreBtn.closest('.module-card');
                    if (deleteInput && moduleCard) {
                        deleteInput.value = '0';
                        moduleCard.classList.remove('bg-danger', 'bg-opacity-10');
                        moduleCard.style.opacity = '1';
                        restoreBtn.previousSibling.style.display = 'inline-block';
                        restoreBtn.remove();
                    }
                }
            }
        });

        // Handle question delete and restore buttons using event delegation
        document.addEventListener('click', function(e) {
            // Handle delete button clicks
            if (e.target.closest('.remove-question-btn')) {
                const btn = e.target.closest('.remove-question-btn');
                const questionId = btn.getAttribute('data-question-id');
                const questionCard = btn.closest('.question-card');
                
                if (questionId && questionCard) {
                    // For existing questions, mark for deletion
                    const deleteInput = document.getElementById('delete_question_' + questionId);
                    if (deleteInput) {
                        deleteInput.value = '1';
                        questionCard.classList.add('bg-danger', 'bg-opacity-10');
                        questionCard.style.opacity = '0.7';
                        
                        // Add a restore button
                        const restoreBtn = document.createElement('button');
                        restoreBtn.type = 'button';
                        restoreBtn.className = 'btn btn-sm btn-success restore-question-btn ms-2';
                        restoreBtn.innerHTML = '<i class="fas fa-undo"></i>';
                        restoreBtn.setAttribute('data-question-id', questionId);
                        
                        btn.parentNode.insertBefore(restoreBtn, btn.nextSibling);
                        btn.style.display = 'none';
                    }
                } else {
                    // For new questions, just remove the card
                    questionCard?.remove();
                }
            }
            // Handle restore button clicks
            else if (e.target.closest('.restore-question-btn')) {
                const restoreBtn = e.target.closest('.restore-question-btn');
                const questionId = restoreBtn.getAttribute('data-question-id');
                if (questionId) {
                    const deleteInput = document.getElementById('delete_question_' + questionId);
                    const questionCard = restoreBtn.closest('.question-card');
                    if (deleteInput && questionCard) {
                        deleteInput.value = '0';
                        questionCard.classList.remove('bg-danger', 'bg-opacity-10');
                        questionCard.style.opacity = '1';
                        restoreBtn.previousSibling.style.display = 'inline-block';
                        restoreBtn.remove();
                    }
                }
            }
        });

        // Handle question type changes using event delegation
        document.addEventListener('change', function(e) {
            if (e.target.classList.contains('question-type-select')) {
                const select = e.target;
                const answersContainer = select.closest('.question-card').querySelector('.answers-container');
                const questionId = select.closest('.question-card').getAttribute('data-question-id');
                
                if (answersContainer) {
                    if (select.value === 'true_false') {
                        // For true/false questions, show only two fixed options
                        answersContainer.innerHTML = `
                            <div class="answer-item mb-2">
                                <div class="input-group">
                                    <div class="input-group-text">
                                        <input type="radio" name="correct_answer_${questionId}" value="0" required>
                                    </div>
                                    <input type="text" class="form-control" name="answer_text_${questionId}[]" value="صح" readonly>
                                </div>
                            </div>
                            <div class="answer-item mb-2">
                                <div class="input-group">
                                    <div class="input-group-text">
                                        <input type="radio" name="correct_answer_${questionId}" value="1" required>
                                    </div>
                                    <input type="text" class="form-control" name="answer_text_${questionId}[]" value="خطأ" readonly>
                                </div>
                            </div>
                        `;
                    } else if (select.value === 'short_answer') {
                        // For short answer questions, show a single text input for the correct answer
                        answersContainer.innerHTML = `
                            <div class="answer-item mb-2">
                                <div class="input-group">
                                    <span class="input-group-text">الإجابة الصحيحة</span>
                                    <input type="text" class="form-control" name="answer_text_${questionId}[]" required>
                                    <input type="hidden" name="correct_answer_${questionId}" value="0">
                                </div>
                            </div>
                        `;
                    } else {
                        // For multiple choice questions, allow adding multiple answers
                        answersContainer.innerHTML = `
                            <div class="answer-item mb-2">
                                <div class="input-group">
                                    <div class="input-group-text">
                                        <input type="radio" name="correct_answer_${questionId}" value="0" required>
                                    </div>
                                    <input type="text" class="form-control" name="answer_text_${questionId}[]" placeholder="أدخل الإجابة" required>
                                    <button type="button" class="btn btn-outline-danger remove-answer-btn">
                                        <i class="fas fa-times"></i>
                                    </button>
                                </div>
                            </div>
                            <button type="button" class="btn btn-outline-primary btn-sm add-answer-btn mt-2">
                                <i class="fas fa-plus me-1"></i>إضافة إجابة
                            </button>
                        `;
                        
                        // Show add answer button
                        const addAnswerBtn = select.closest('.question-card').querySelector('.add-answer-btn');
                        if (addAnswerBtn) {
                            addAnswerBtn.style.display = 'inline-block';
                        }
                    }
                }
            }
        });

        // Initialize answer handlers for existing multiple choice questions
        document.querySelectorAll('.answers-container').forEach(container => {
            const questionCard = container.closest('.question-card');
            if (questionCard) {
                const typeSelect = questionCard.querySelector('.question-type-select');
                if (typeSelect && typeSelect.value === 'multiple_choice') {
                    initializeAnswerHandlers(container);
                }
            }
        });


        // Function to initialize answer handlers using event delegation
        function initializeAnswerHandlers(container) {
            // Handle add answer button clicks
            container.addEventListener('click', function(e) {
                const addAnswerBtn = e.target.closest('.add-answer-btn');
                if (addAnswerBtn) {
                    const questionId = addAnswerBtn.closest('.question-card').getAttribute('data-question-id');
                    const answersCount = container.querySelectorAll('.answer-item').length;
                    
                    const newAnswerHtml = `
                        <div class="answer-item mb-2">
                            <div class="input-group">
                                <div class="input-group-text">
                                    <input type="radio" name="correct_answer_${questionId}" value="${answersCount}" required>
                                </div>
                                <input type="text" class="form-control" name="answer_text_${questionId}[]" placeholder="أدخل الإجابة" required>
                                <button type="button" class="btn btn-outline-danger remove-answer-btn">
                                    <i class="fas fa-times"></i>
                                </button>
                            </div>
                        </div>
                    `;
                    
                    addAnswerBtn.insertAdjacentHTML('beforebegin', newAnswerHtml);
                }

                // Handle remove answer button clicks
                const removeAnswerBtn = e.target.closest('.remove-answer-btn');
                if (removeAnswerBtn) {
                    const answerId = removeAnswerBtn.getAttribute('data-answer-id');
                    const answerItem = removeAnswerBtn.closest('.answer-item');
                    
                    if (answerId && answerItem) {
                        // For existing answers, mark for deletion
                        const deleteInput = document.getElementById('delete_answer_' + answerId);
                        if (deleteInput) {
                            deleteInput.value = '1';
                            answerItem.classList.add('bg-danger', 'bg-opacity-10');
                            answerItem.style.opacity = '0.7';
                            
                            // Add restore button
                            const restoreBtn = document.createElement('button');
                            restoreBtn.type = 'button';
                            restoreBtn.className = 'btn btn-outline-success restore-answer-btn';
                            restoreBtn.innerHTML = '<i class="fas fa-undo"></i>';
                            restoreBtn.setAttribute('data-answer-id', answerId);
                            
                            removeAnswerBtn.parentNode.insertBefore(restoreBtn, removeAnswerBtn.nextSibling);
                            removeAnswerBtn.style.display = 'none';
                        }
                    } else if (answerItem) {
                        // For new answers, remove the element and update remaining answer indices
                        answerItem.remove();
                        
                        const questionCard = removeAnswerBtn.closest('.question-card');
                        if (questionCard) {
                            const questionId = questionCard.getAttribute('data-question-id');
                            questionCard.querySelectorAll('.answer-item').forEach((answer, index) => {
                                const radio = answer.querySelector(`input[name="correct_answer_${questionId}"]`);
                                if (radio) radio.value = index;
                            });
                        }
                    }
                }

                // Handle restore answer button clicks
                const restoreAnswerBtn = e.target.closest('.restore-answer-btn');
                if (restoreAnswerBtn) {
                    const answerId = restoreAnswerBtn.getAttribute('data-answer-id');
                    const answerItem = restoreAnswerBtn.closest('.answer-item');
                    if (answerId && answerItem) {
                        const deleteInput = document.getElementById('delete_answer_' + answerId);
                        if (deleteInput) {
                            deleteInput.value = '0';
                            answerItem.classList.remove('bg-danger', 'bg-opacity-10');
                            answerItem.style.opacity = '1';
                            restoreAnswerBtn.previousSibling.style.display = 'inline-block';
                            restoreAnswerBtn.remove();
                        }
                    }
                }
            });
        }
        
        // Initialize answer handlers for all answer containers
        document.querySelectorAll('.answers-container').forEach(container => {
            initializeAnswerHandlers(container);
        });

        // Handle video name and note remove buttons using event delegation
        document.addEventListener('click', function(e) {
            // Handle video name remove button clicks
            if (e.target.closest('.remove-video-name-btn')) {
                const btn = e.target.closest('.remove-video-name-btn');
                const videoNameItem = btn.closest('.input-group');
                videoNameItem?.remove();
            }
            // Handle note remove button clicks
            else if (e.target.closest('.remove-note-btn')) {
                const btn = e.target.closest('.remove-note-btn');
                const noteItem = btn.closest('.input-group');
                noteItem?.remove();
            }
        });
    }
    // End of initializeDeleteHandlers function

    // Function to initialize quiz toggles
    function initializeQuizToggles() {
        function getQuizSectionId(toggleId) {
            if (toggleId.includes('has_quiz_existing_')) {
                return 'quiz_section_existing_' + toggleId.replace('has_quiz_existing_', '');
            } else if (toggleId.includes('has_quiz_new_')) {
                return 'quiz_section_new_' + toggleId.replace('has_quiz_new_', '');
            }
            return null;
        }

        function toggleQuizSection(toggle) {
            const quizSectionId = getQuizSectionId(toggle.id);
            if (quizSectionId) {
                const quizSection = document.getElementById(quizSectionId);
                if (quizSection) {
                    quizSection.style.display = toggle.checked ? 'block' : 'none';
                }
            }
        }

        // Handle quiz toggle changes using event delegation
        document.addEventListener('change', function(e) {
            if (e.target.classList.contains('quiz-toggle')) {
                toggleQuizSection(e.target);
            }
        });
        
        // Set initial state for all quiz toggles
        document.querySelectorAll('.quiz-toggle').forEach(toggleQuizSection);
    }

    // For add note buttons
    document.addEventListener('click', function(e) {
        if (e.target.closest('.add-note-btn')) {
            const btn = e.target.closest('.add-note-btn');
            const moduleId = btn.getAttribute('data-module-id');
            if (moduleId) {
                console.log(`Adding new note to module ${moduleId}`);
                addNewNote(moduleId);
            }
        }
    });
    
    // Get the modules container
    const modulesContainer = document.getElementById('modules-container');
    if (!modulesContainer) {
        console.warn('Modules container not yet in DOM');
    } else {
        // Get the current number of modules (including deleted ones)
        const updateModuleCount = modulesContainer.querySelectorAll('.module-card').length;
        const newModuleNumber = updateModuleCount + 1;
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
    // End of addNewModule function

    // Function to add a new question
    function addNewQuestion(moduleId) {
        const questionsContainer = document.getElementById(`questions_container_${moduleId}`);
        if (!questionsContainer) return;
    
        // Get the current number of questions
        const questionCount = questionsContainer.querySelectorAll('.question-card').length;
        const newQuestionNumber = questionCount + 1;
        const timestamp = Date.now();
        
        const questionHtml = `
        <div class="card mb-3 question-card" id="question_${moduleId}_${timestamp}" data-question-id="${timestamp}">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h6 class="mb-0">سؤال #${newQuestionNumber}</h6>
                    <button type="button" class="btn btn-sm btn-outline-danger remove-question-btn">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                
                <div class="mb-3">
                    <input type="text" class="form-control question-text" name="question_text_${moduleId}_${timestamp}" placeholder="نص السؤال" required>
                </div>
                
                <div class="mb-3">
                    <select class="form-select question-type" name="question_type_${moduleId}_${timestamp}">
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
                    <i class="fas fa-plus"></i> إضافة إجابة
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
            const typeSelect = newQuestion.querySelector('.question-type');
            if (typeSelect) {
                typeSelect.addEventListener('change', function() {
                    const answersContainer = newQuestion.querySelector('.answers-container');
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
                    const answersContainer = newQuestion.querySelector('.answers-container');
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
        
        // Check if this is an existing question by examining the container ID
        const containerId = answersContainer.id;
        console.log('Adding answer to container:', containerId);
        
        let radioName, textName;
        
        // Handle existing questions (from the database)
        if (containerId.includes('answers_existing_question_')) {
            // Format: answers_existing_question_123
            const questionIdMatch = containerId.match(/answers_existing_question_(\d+)/);
            if (questionIdMatch) {
                questionId = questionIdMatch[1];
                console.log('Found existing question ID:', questionId);
                
                // Set the correct name attributes for existing questions
                radioName = `correct_answer_existing_${questionId}`;
                textName = `answer_text_existing_${questionId}_${newAnswerNumber}`;
            }
        } else {
            // This is a new question
            // Use the provided moduleId and questionId
            radioName = `correct_answer_${moduleId}_${questionId}`;
            textName = `answer_text_${moduleId}_${questionId}_${newAnswerNumber}`;
        }
        
        console.log(`Creating new answer with radio name: ${radioName} and text name: ${textName}`);
        
        // Create the answer HTML
        const answerHtml = `
        <div class="answer-item mb-2">
            <div class="input-group">
                <div class="input-group-text">
                    <input class="form-check-input mt-0" type="radio" name="${radioName}" value="${newAnswerNumber}">
                </div>
                <input type="text" class="form-control" name="${textName}" placeholder="الإجابة ${newAnswerNumber + 1}" required>
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
    // Validate form first
    if (!validateForm()) {
        return false;
    }
    
    // Check if any PDF is marked for deletion and handle file inputs accordingly
    const pdfTypes = ['syllabus_pdf', 'materials_pdf'];
    pdfTypes.forEach(pdfType => {
        const deleteInput = document.getElementById('delete_' + pdfType);
        const fileInput = document.querySelector(`input[name="${pdfType}"]`);
        
        // If marked for deletion and no new file is selected, ensure we keep the delete flag
        if (deleteInput && deleteInput.value === '1' && fileInput && fileInput.files.length === 0) {
            // The delete flag is already set, no need to do anything
            console.log(`${pdfType} marked for deletion`);
        } 
        // If a new file is selected, make sure the delete flag is reset
        else if (fileInput && fileInput.files.length > 0 && deleteInput) {
            deleteInput.value = '0';
            console.log(`New ${pdfType} selected, resetting delete flag`);
        }
    });
    
    // Collect module data
    const modules = [];
    document.querySelectorAll('.module-card').forEach((moduleCard, index) => {
        // Skip modules marked for deletion
        const deleteFlagInput = moduleCard.querySelector('input[id^="delete_module_"]');
        if (deleteFlagInput && deleteFlagInput.value === '1') {
            console.log(`Module card ${moduleCard.id} marked for deletion, skipping`);
            return; // Skip this module as it's marked for deletion
        }

        // Determine module identifier and whether it's an existing module or a new one
        let moduleId = '';
        let isExisting = false;
        if (moduleCard.id.startsWith('existing_module_')) {
            moduleId = moduleCard.id.replace('existing_module_', '');
            isExisting = true;
        } else if (moduleCard.id.startsWith('new_module_')) {
            moduleId = moduleCard.id.replace('new_module_', '');
            isExisting = false;
        } else if (moduleCard.id.startsWith('module_')) { // Fallback/legacy pattern
            moduleId = moduleCard.id.replace('module_', '');
            isExisting = /^\d+$/.test(moduleId);
        }

        // Safely fetch inputs within the current module card
        const nameInput = moduleCard.querySelector('input[name^="module_name_"]');
        const descInput = moduleCard.querySelector('textarea[name^="module_description_"]');
        const quizToggle = moduleCard.querySelector('.quiz-toggle');

        // Build module data object
        const moduleData = {
            id: moduleId,
            name: nameInput ? nameInput.value : '',
            description: descInput ? descInput.value : '',
            number: index + 1,
            has_quiz: quizToggle ? quizToggle.checked : false
        };

        // Add quiz data if the module has a quiz
        if (moduleData.has_quiz) {
            const quizSection = moduleCard.querySelector('.quiz-section');
            if (quizSection) {
                const quizData = {
                    title: (quizSection.querySelector('[name^="quiz_title_"]') || {}).value || '',
                    description: (quizSection.querySelector('[name^="quiz_description_"]') || {}).value || '',
                    pass_mark: (quizSection.querySelector('[name^="quiz_pass_mark_"]') || {}).value || '',
                    time_limit: (quizSection.querySelector('[name^="quiz_time_limit_"]') || {}).value || '',
                    questions: []
                };

                // Collect questions data
                quizSection.querySelectorAll('.question-card').forEach((questionCard) => {
                    const questionId = questionCard.getAttribute('data-question-id');
                    const questionTextInput = questionCard.querySelector('input[name^="question_text"]');
                    const questionText = questionTextInput ? questionTextInput.value : '';
                    
                    const questionTypeSelect = questionCard.querySelector('select[name^="question_type"]');
                    const questionType = questionTypeSelect ? questionTypeSelect.value : 'multiple_choice';
                    
                    const questionData = {
                        id: questionId,
                        text: questionText,
                        type: questionType,
                        answers: []
                    };

                    // Helper to safely get correct answer value
                    const getCheckedRadioValue = () => {
                        const radioChecked = questionCard.querySelector('input[name^="correct_answer"]:checked');
                        return radioChecked ? radioChecked.value : null;
                    };

                    if (questionType === 'true_false') {
                        const correctAnswer = getCheckedRadioValue() || '0';
                        questionData.answers.push(
                            { text: 'صح', is_correct: correctAnswer === '0' },
                            { text: 'خطأ', is_correct: correctAnswer === '1' }
                        );
                    } else if (questionType === 'short_answer') {
                        const answerTextInput = questionCard.querySelector('input[name^="answer_text"]');
                        const answerText = answerTextInput ? answerTextInput.value : '';
                        questionData.answers.push({ text: answerText, is_correct: true });
                    } else {
                        const correctAnswer = getCheckedRadioValue();
                        questionCard.querySelectorAll('.answer-item').forEach((answerItem, index) => {
                            const answerTextInput = answerItem.querySelector('input[name^="answer_text"]');
                            const answerText = answerTextInput ? answerTextInput.value : '';
                            questionData.answers.push({
                                text: answerText,
                                is_correct: correctAnswer ? index.toString() === correctAnswer : false
                            });
                        });
                    }

                    quizData.questions.push(questionData);
                });

                moduleData.quiz = quizData;
            }
        }
        
        modules.push(moduleData);
    });
    
    // Add modules data as JSON to the form
    const modulesInput = document.getElementById('modules_data');
    if (!modulesInput) {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'modules';
        input.id = 'modules_data';
        input.value = JSON.stringify(modules);
        document.getElementById('course-form').appendChild(input);
    } else {
        modulesInput.value = JSON.stringify(modules);
    }
    
    // Process module data before submission
    const moduleCards = document.querySelectorAll('.module-card');
    moduleCards.forEach(moduleCard => {
        // Handle module deletion flags
        const moduleId = moduleCard.id.replace('module_', '');
        const deleteModuleInput = document.getElementById(`delete_module_${moduleId}`);
        
        if (deleteModuleInput && deleteModuleInput.value === '1') {
            console.log(`Module ${moduleId} marked for deletion`);
        }
        
        // Handle quiz sections
        const isExisting = moduleId.match(/^\d+$/) !== null;
        const quizToggleId = isExisting ? `has_quiz_existing_${moduleId}` : `has_quiz_new_${moduleId}`;
        const quizToggle = document.getElementById(quizToggleId);
        const quizSection = moduleCard.querySelector('.quiz-section');
        
        if (quizToggle && quizSection) {
            // Important: Always make quiz sections visible during form submission
            // This ensures all form fields are included in the submission
            // The server will check the toggle value to determine if the quiz should be saved
            quizSection.style.display = 'block';
            console.log(`Ensuring quiz section for module ${moduleId} is visible for form submission`);
        }
    });
    
    // Ensure all form data is included by checking required fields
    const form = document.getElementById('course-form');
    const requiredFields = form.querySelectorAll('[required]');
    let missingFields = false;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            console.error(`Required field missing: ${field.name}`);
            field.classList.add('is-invalid');
            missingFields = true;
        }
    });
    
    if (missingFields) {
        alert('يرجى ملء جميع الحقول المطلوبة');
        return false;
    }
    
    // Use FormData to ensure proper file upload
    const formData = new FormData(form);
    
    // Add a flag to indicate this is a form submission
    formData.append('is_form_submit', 'true');
    
    // Debug: Log all form data being submitted
    console.log('Submitting form with the following data:');
    for (let [key, value] of formData.entries()) {
        if (typeof value !== 'object') { // Don't log file objects
            console.log(`${key}: ${value}`);
        } else {
            console.log(`${key}: [File object]`);
        }
    }
    
    // Show loading indicator
    const submitBtn = document.getElementById('submit-course-btn');
    const originalBtnText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> جاري الحفظ...`;
    
    // Submit the form using fetch API to handle file uploads properly
    fetch(form.action || window.location.href, {
        method: 'POST',
        body: formData,
        // Don't set Content-Type header - browser will set it with boundary for multipart/form-data
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Server responded with status: ${response.status}`);
        }
        return response.text();
    })
    .then(html => {
        // Check if response contains success message
        if (html.includes('success') || html.includes('تم تحديث')) {
            // Redirect to dashboard after successful update
            window.location.href = '/dashboard/';
        } else {
            // If it's a form with errors, replace the page content
            document.open();
            document.write(html);
            document.close();
        }
    })
    .catch(error => {
        console.error('Error submitting form:', error);
        alert('حدث خطأ أثناء حفظ الدورة. يرجى المحاولة مرة أخرى.');
        // Restore button state
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalBtnText;
    });
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

// =============================
// Step Navigation for Update Page
// =============================
let currentStepIndex = 0;

function showStep(stepIdx) {
    const stepCards = document.querySelectorAll('.step-card');
    if (!stepCards.length) return;
    stepCards.forEach((card, idx) => {
        if (idx === stepIdx) {
            card.classList.remove('d-none');
        } else {
            card.classList.add('d-none');
        }
    });
    currentStepIndex = stepIdx;
}

function nextStep() {
    const stepCards = document.querySelectorAll('.step-card');
    if (currentStepIndex < stepCards.length - 1) {
        showStep(currentStepIndex + 1);
    }
}

function prevStep() {
    if (currentStepIndex > 0) {
        showStep(currentStepIndex - 1);
    }
}

// Expose to global scope for inline onclick handlers
window.nextStep = nextStep;
window.prevStep = prevStep;

// Ensure first step is visible on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => showStep(0));
} else {
    showStep(0);
}

// End of file


// Module functions
function addModule() {
    moduleCount++;
    const moduleId = `module_${moduleCount}`;
  
    const template = document.getElementById('module-template');
    if (!template) {
      console.error('Module template not found');
      return;
    }
  
    const moduleElement = template.content.cloneNode(true).firstElementChild;
    moduleElement.id = moduleId;
  
    // Set module title in the header
    const titleElement = moduleElement.querySelector('.card-header h5');
    if (titleElement) {
      titleElement.innerHTML = `<i class="fas fa-layer-group text-primary me-2"></i>الموديول ${moduleCount}`;
    }
    
    // Set up module name input
    const moduleNameInput = moduleElement.querySelector('input[name^="module_name"]');
    if (moduleNameInput) {
      moduleNameInput.required = true;
      moduleNameInput.placeholder = `أدخل اسم الموديول ${moduleCount}`;
    } else {
      console.error('Module name input not found in template');
    }
  
    // Add module to container
    const container = document.getElementById('modules-container');
    if (container) {
      container.appendChild(moduleElement);
      // Add a question by default when quiz is enabled
      const quizToggle = moduleElement.querySelector('.quiz-toggle');
      if (quizToggle) {
        quizToggle.addEventListener('change', function() {
          toggleQuiz(moduleElement, this.checked);
          if (this.checked) {
            addQuestion(moduleElement);
          }
        });
      }
      // Get the module title element
      const moduleTitle = moduleElement.querySelector('.card-header h5');
      if (moduleTitle) {
        moduleTitle.innerHTML = `<i class="fas fa-layer-group text-primary me-2"></i>الموديول ${moduleCount}`;
      }
    } else {
      console.error('Modules container not found');
      return;
    }
    
    // Update PDF input names
    const pdfInputs = moduleElement.querySelectorAll('.pdf-files-container input[type="file"]');
    pdfInputs.forEach((input, index) => {
      input.name = `module_${moduleCount}_pdf[]`;
    });
    
    // Update additional materials input names
    const materialInputs = moduleElement.querySelectorAll('.materials-container input[type="file"]');
    materialInputs.forEach((input, index) => {
      input.name = `module_${moduleCount}_materials[]`;
    });
    
    // Update video name input
    const videoNameInputs = moduleElement.querySelectorAll('.video-titles-container input[type="text"]');
    videoNameInputs.forEach((input, index) => {
      input.name = `module_${moduleCount}_video_title_${index}`;
    });
    
    // Update quiz toggle ID and label
    const quizToggle = moduleElement.querySelector('.quiz-toggle');
    if (quizToggle) {
      quizToggle.id = `quiz_toggle_${moduleId}`;
      const quizLabel = moduleElement.querySelector('.form-check-label');
      if (quizLabel) {
        quizLabel.setAttribute('for', `quiz_toggle_${moduleId}`);
      }
      
      // Initialize quiz toggle state
      quizToggle.checked = false;
      
      // Initialize quiz section visibility
      const quizSection = moduleElement.querySelector('.quiz-section');
      if (quizSection) {
        quizSection.style.display = 'none';
        
        // Set module ID for the add question button
        const addQuestionBtn = quizSection.querySelector('.add-question-btn');
        if (addQuestionBtn) {
          addQuestionBtn.setAttribute('data-module-id', moduleId);
        }
      }
    }
    
    // Add the module to the container
    const modulesContainer = document.getElementById('modules-container');
    modulesContainer.appendChild(moduleElement);
    
    // Setup event listeners
    setupModuleEventListeners(moduleElement, moduleId);
  }
  
  function setupModuleEventListeners(moduleElement, moduleId) {
    // Remove module button
    const removeModuleBtn = moduleElement.querySelector('.remove-module-btn');
    if (removeModuleBtn) {
      removeModuleBtn.addEventListener('click', function() {
        removeModule(moduleId);
      });
    }
  
    console.log('Setting up module event listeners:', { moduleId });
  
    // Set up PDF file input change event
    const pdfInput = moduleElement.querySelector('input[type="file"][accept=".pdf"]');
    if (pdfInput) {
      pdfInput.addEventListener('change', function() {
        if (this.files.length > 0) {
          const fileName = this.files[0].name;
          
          // Auto-populate the title field
          const titleInput = moduleElement.querySelector('.pdf-title');
          if (titleInput && !titleInput.value) {
            titleInput.value = fileName.replace(/\.pdf$/i, '');
          }
          
          // Show file name
          const fileNameSpan = document.createElement('span');
          fileNameSpan.className = 'selected-file-name mt-1 mb-2 text-primary';
          fileNameSpan.style.display = 'block';
          fileNameSpan.innerHTML = `<i class="fas fa-file-pdf me-1"></i>${fileName}`;
          
          // Remove any existing file name display
          const existingFileName = this.nextElementSibling;
          if (existingFileName && existingFileName.classList.contains('selected-file-name')) {
            existingFileName.remove();
          }
          
          // Add file name after input
          this.insertAdjacentElement('afterend', fileNameSpan);
        }
      });
    }
  
    // Add material button
    const addMaterialBtn = moduleElement.querySelector('.add-material-btn');
    if (addMaterialBtn) {
      addMaterialBtn.addEventListener('click', () => addMaterial(moduleElement, moduleId));
    }
  
    // Add note button
    const addNoteBtn = moduleElement.querySelector('.add-note-btn');
    if (addNoteBtn) {
      addNoteBtn.addEventListener('click', () => addNote(moduleElement, moduleId));
    }
  
    // Add video name button
    const addVideoNameBtn = moduleElement.querySelector('.add-title-btn');
    if (addVideoNameBtn) {
      addVideoNameBtn.addEventListener('click', () => addVideoName(moduleElement, moduleId));
    }
  
    // Add question button
    // Add question button
    const quizSection = moduleElement.querySelector('.quiz-section');
    if (quizSection) {
      const addQuestionBtn = quizSection.querySelector('.add-question-btn');
      if (addQuestionBtn) {
        addQuestionBtn.setAttribute('data-module-id', moduleId);
        addQuestionBtn.addEventListener('click', () => addQuestion(moduleElement, moduleId));
      }
    }
  
    // Quiz toggle
    const quizToggle = moduleElement.querySelector('.quiz-toggle');
    if (quizToggle) {
      console.log('Found quiz toggle');
      quizToggle.addEventListener('change', function() {
        console.log('Quiz toggle changed for module:', moduleId, 'checked:', this.checked);
        toggleQuiz(moduleElement, this.checked);
      });
    } else {
      console.error('Quiz toggle not found in module:', moduleId);
    }
  }
  
  function removeModule(moduleId) {
    const moduleElement = document.getElementById(moduleId);
    if (moduleElement) {
      // If this is an existing module, mark it for deletion instead of removing it
      if (moduleId.startsWith('existing_module_')) {
        const realModuleId = moduleId.replace('existing_module_', '');
        const deleteInput = document.getElementById(`delete_module_${realModuleId}`);
        if (deleteInput) {
          deleteInput.value = '1';
          moduleElement.style.display = 'none';
        } else {
          moduleElement.remove();
        }
      } else {
        moduleElement.remove();
      }
    }
  }
  
  function toggleQuiz(moduleElement, isChecked) {
    console.log('Toggling quiz:', { moduleId: moduleElement.id, isChecked });
    
    if (!moduleElement) {
      console.error('Module element is required');
      return;
    }
  
    const quizSection = moduleElement.querySelector('.quiz-section');
    if (!quizSection) {
      console.error('Quiz section not found');
      return;
    }
  
    const questionsContainer = quizSection.querySelector('.questions-container');
    if (!questionsContainer) {
      console.error('Questions container not found');
      return;
    }
  
    // Toggle quiz section visibility
    quizSection.style.display = isChecked ? 'block' : 'none';
  
    if (isChecked) {
      // Add first question if none exist
      const visibleQuestions = Array.from(questionsContainer.querySelectorAll('.question-card'))
        .filter(q => q.style.display !== 'none');
  
      if (visibleQuestions.length === 0) {
        const moduleId = moduleElement.id;
        if (!moduleId) {
          console.error('Module ID not found');
          return;
        }
        console.log('Adding initial question for module:', moduleId);
        addQuestion(moduleElement, moduleId);
      } else {
        console.log('Questions already exist, not adding new one');
      }
    } else {
      console.log('Hiding quiz section');
    };
    
    // Remove the duplicate toggleQuiz function that appears later in the file
    window.toggleQuiz = function(moduleElement, isChecked) {
      console.log('Toggling quiz (global):', { moduleId: moduleElement.id, isChecked });
      
      const quizSection = moduleElement.querySelector('.quiz-section');
      if (quizSection) {
        quizSection.style.display = isChecked ? 'block' : 'none';
        
        if (isChecked) {
          const questionsContainer = quizSection.querySelector('.questions-container');
          if (questionsContainer && questionsContainer.querySelectorAll('.question-card').length === 0) {
            addQuestion(moduleElement, moduleElement.id);
          }
        }
      }
    }
  }
  
  // Question and Answer functions
  window.addQuestion = function(moduleElement, moduleId) {
    const questionId = `q_${Date.now()}`; // Generate unique question ID
    const questionCard = document.createElement('div');
    questionCard.className = 'card mb-3 question-card';
    questionCard.dataset.questionId = questionId;
    
    questionCard.innerHTML = `
      <div class="card-body">
        <div class="d-flex justify-content-between mb-3">
          <h6 class="card-title">السؤال <span class="question-number"></span></h6>
          <button type="button" class="btn btn-sm btn-outline-danger" onclick="window.removeQuestion(this.closest('.question-card'))">
            <i class="fas fa-trash"></i> حذف السؤال
          </button>
        </div>
        <div class="mb-3">
          <label class="form-label">نوع السؤال</label>
          <select class="form-select question-type" onchange="window.updateQuestionType(this)">
            <option value="mcq">اختيار من متعدد</option>
            <option value="true_false">صح أو خطأ</option>
            <option value="short_answer">مقالي</option>
          </select>
        </div>
        <div class="mb-3">
          <label class="form-label">نص السؤال</label>
          <input type="text" class="form-control question-text" name="question_${questionId}_text" required>
        </div>
        <div class="mb-3">
          <label class="form-label">درجة السؤال</label>
          <input type="number" class="form-control question-points" name="question_${questionId}_points" min="1" value="1" required>
        </div>
        <div class="answers-container mb-2">
          <!-- Answers will be added here -->
        </div>
      </div>
    `;
  
    // Find the questions container in the module
    const questionsContainer = moduleElement.querySelector('.questions-container');
    if (!questionsContainer) {
      console.error('Questions container not found');
      return null;
    }
    
    questionsContainer.appendChild(questionCard);
    
    // Initialize question type after the element is in the DOM
    setTimeout(() => {
      const questionTypeSelect = questionCard.querySelector('.question-type');
      if (questionTypeSelect) {
        updateQuestionType(questionTypeSelect);
      } else {
        console.error('Could not find question type select element');
      }
    }, 0);
    
    return questionCard;
  }
  
  window.updateQuestionType = function(selectElement) {
    if (!selectElement) {
      console.error('selectElement is null or undefined');
      return;
    }
    
    const questionCard = selectElement.closest('.question-card');
    if (!questionCard) {
      console.error('Could not find parent question-card element');
      return;
    }
    
    const questionId = questionCard.dataset.questionId;
    const answersContainer = questionCard.querySelector('.answers-container');
    if (!answersContainer) {
      console.error('Could not find answers container');
      return;
    }
    
    const questionType = selectElement.value;
    
    // Clear existing answers
    answersContainer.innerHTML = '';
    
    // Add hidden input for question type
    const typeInput = document.createElement('input');
    typeInput.type = 'hidden';
    typeInput.name = `question_${questionId}_type`;
    typeInput.value = questionType;
    answersContainer.appendChild(typeInput);
    
    if (questionType === 'true_false') {
      // Add true/false options
      const trueFalseTemplate = `
        <div class="answer-card card mb-2">
          <div class="card-body p-2">
            <div class="form-check">
              <input class="form-check-input answer-correct" type="radio" 
                     name="question_${questionId}_correct" value="true" required>
              <label class="form-check-label">
                صح
              </label>
            </div>
          </div>
        </div>
        <div class="answer-card card mb-2">
          <div class="card-body p-2">
            <div class="form-check">
              <input class="form-check-input answer-correct" type="radio" 
                     name="question_${questionId}_correct" value="false" required>
              <label class="form-check-label">
                خطأ
              </label>
            </div>
          </div>
        </div>
      `;
      answersContainer.insertAdjacentHTML('beforeend', trueFalseTemplate);
    } 
    else if (questionType === 'short_answer') {
      // Add short answer field
      const shortAnswerTemplate = `
        <div class="mb-3">
          <input type="text" class="form-control" 
                 name="question_${questionId}_answer" 
                 placeholder="إجابة قصيرة" required>
        </div>
      `;
      answersContainer.insertAdjacentHTML('beforeend', shortAnswerTemplate);
    } 
    else {
      // Default to multiple choice - add 2 empty answers by default
      for (let i = 0; i < 2; i++) {
        const answerId = `a_${Date.now()}_${i}`;
        const answerHtml = `
          <div class="answer-card card mb-2" data-answer-id="${answerId}">
            <div class="card-body p-2">
              <div class="d-flex align-items-center">
                <div class="form-check me-2">
                  <input class="form-check-input answer-correct" type="radio" 
                         name="question_${questionId}_correct" 
                         value="${i}" ${i === 0 ? 'checked' : ''} required>
                </div>
                <input type="text" class="form-control form-control-sm answer-text" 
                       name="question_${questionId}_answers[]" 
                       placeholder="نص الإجابة" required>
                <button type="button" class="btn btn-sm btn-outline-danger ms-2" 
                        onclick="window.removeAnswer(this, this.closest('.answer-card'))">
                  <i class="fas fa-trash"></i>
                </button>
              </div>
            </div>
          </div>`;
        answersContainer.insertAdjacentHTML('beforeend', answerHtml);
      }
      
      // Add "Add Answer" button for MCQ
      const addButton = document.createElement('button');
      addButton.type = 'button';
      addButton.className = 'btn btn-sm btn-outline-primary mt-2 add-answer-btn';
      addButton.innerHTML = '<i class="fas fa-plus me-1"></i> إضافة إجابة';
      addButton.onclick = () => window.addAnswer(questionCard, questionId);
      answersContainer.appendChild(addButton);
    }
  }
  
  window.addAnswer = function(questionElement, questionId) {
    if (!questionElement) {
      console.error('Question element is null or undefined');
      return null;
    }
  
    const answersContainer = questionElement.querySelector('.answers-container');
    if (!answersContainer) {
      console.error('Answers container not found');
      return null;
    }
  
    const answerCards = answersContainer.querySelectorAll('.answer-card');
    const answerCount = answerCards.length;
    
    // Check if we've reached the maximum number of answers
    const MAX_ANSWERS = 6;
    if (answerCount >= MAX_ANSWERS) {
      showAlert('warning', `لا يمكن إضافة أكثر من ${MAX_ANSWERS} إجابات`);
      return null;
    }
    
    const answerId = `a_${Date.now()}_${answerCount}`;
    const answerNumber = answerCount;
    
    const answerHtml = `
      <div class="answer-card card mb-2" data-answer-id="${answerId}">
        <div class="card-body p-2">
          <div class="d-flex align-items-center">
            <div class="form-check me-2">
              <input class="form-check-input answer-correct" type="radio" 
                     name="question_${questionId}_correct" 
                     value="${answerNumber}" 
                     ${answerNumber === 0 ? 'checked' : ''}>
            </div>
            <input type="text" class="form-control form-control-sm answer-text" 
                   name="question_${questionId}_answers[]" 
                   placeholder="نص الإجابة" required>
            <button type="button" class="btn btn-sm btn-outline-danger ms-2" 
                    onclick="window.removeAnswer(this, this.closest('.answer-card'))">
              <i class="fas fa-trash"></i>
            </button>
          </div>
        </div>
      </div>`;
      
    // Insert before the "Add Answer" button
    const addButton = answersContainer.querySelector('.add-answer-btn');
    if (addButton) {
      addButton.insertAdjacentHTML('beforebegin', answerHtml);
    } else {
      answersContainer.insertAdjacentHTML('beforeend', answerHtml);
    }
    
    // Focus the new answer input
    const newInput = document.querySelector(`[data-answer-id="${answerId}"] .answer-text`);
    if (newInput) {
      newInput.focus();
    }
    
    return document.querySelector(`[data-answer-id="${answerId}"]`);
  };
  
  window.removeAnswer = function(button, answerElement) {
    if (!answerElement) return;
    
    const answersContainer = answerElement.closest('.answers-container');
    if (!answersContainer) return;
    
    const answerCards = answersContainer.querySelectorAll('.answer-card');
    
    // Don't remove if there are only 2 answers left
    if (answerCards.length <= 2) {
      showAlert('warning', 'يجب أن يحتوي السؤال على إجابتين على الأقل');
      return;
    }
    
    // Check if the answer being removed is the currently selected correct answer
    const isRemovingCorrect = answerElement.querySelector('input[type="radio"]:checked') !== null;
    
    // Remove the answer
    answerElement.remove();
    
    // If we removed the correct answer, select the first remaining answer
    if (isRemovingCorrect) {
      const firstRadio = answersContainer.querySelector('input[type="radio"]');
      if (firstRadio) {
        firstRadio.checked = true;
      }
    }
    
    // Update answer values to maintain correct indices
    const remainingAnswers = answersContainer.querySelectorAll('.answer-card');
    remainingAnswers.forEach((card, index) => {
      const radio = card.querySelector('input[type="radio"]');
      if (radio) {
        radio.value = index;
        radio.name = `question_${card.closest('.question-card').dataset.questionId}_correct`;
      }
      
      const textInput = card.querySelector('input[type="text"]');
      if (textInput) {
        textInput.name = `question_${card.closest('.question-card').dataset.questionId}_answers[]`;
      }
    });
  };
  
  window.removeQuestion = function(questionElement) {
    if (!questionElement) return;
    
    const questionsContainer = questionElement.closest('.questions-container');
    if (!questionsContainer) return;
    
    const questionCards = questionsContainer.querySelectorAll('.question-card');
    
    // Don't remove if there's only one question left
    if (questionCards.length <= 1) {
      showAlert('warning', 'يجب أن يحتوي الموديول على سؤال واحد على الأقل');
      return;
    }
    
    // Remove the question
    questionElement.remove();
    
    // Update question numbers
    const remainingQuestions = questionsContainer.querySelectorAll('.question-card');
    remainingQuestions.forEach((card, index) => {
      const questionNumber = card.querySelector('.question-number');
      if (questionNumber) {
        questionNumber.textContent = index + 1;
      }
    });
  };
  
  function toggleQuiz(moduleElement, isChecked) {
    const quizSection = moduleElement.querySelector('.quiz-section');
    if (!quizSection) return;
    
    if (isChecked) {
      quizSection.style.display = 'block';
    } else {
      quizSection.style.display = 'none';
    }
  }
  