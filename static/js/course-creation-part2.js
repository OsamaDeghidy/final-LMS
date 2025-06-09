
// Submit the course form
function submitCourse() {
  if (!validateForm()) {
    showAlert('danger', 'يرجى ملء جميع الحقول المطلوبة قبل الحفظ');
    return;
  }

  const formData = new FormData(document.getElementById('course-form'));
  const submitBtn = document.getElementById('submit-course-btn');
  const originalText = submitBtn.innerHTML;
  submitBtn.disabled = true;
  let isValid = true; // Initialize isValid variable

  // Show loading state
  submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>جاري الحفظ...';
  
  // Make sure course image is included
  const courseImageInput = document.querySelector('input[name="course_image"]');
  if (courseImageInput && courseImageInput.files.length > 0) {
    console.log('Adding course image:', courseImageInput.files[0].name);
    // formData will already include this from the form, but log it for confirmation
  } else {
    console.log('No course image selected');
  }

  // Process modules
  const modules = document.querySelectorAll('.module-card:not([style*="display: none"])');
  let moduleIndex = 0;

  if (modules.length === 0) {
    showAlert('danger', 'يجب إضافة موديول واحد على الأقل');
    submitBtn.disabled = false;
    submitBtn.innerHTML = originalText;
    return;
  }
  
  // Add total module count to formData
  formData.append('total_module_count', modules.length);

  modules.forEach(module => {
    if (module.style.display === 'none') return; // Skip hidden modules

    moduleIndex++;
    const moduleId = module.id;
    console.log('Processing module:', { moduleId, moduleIndex });

    // Process module title
    const titleInput = module.querySelector('input[name^="module_title"]');
    if (titleInput) {
      formData.append(`module_${moduleIndex}_title`, titleInput.value);
    }

    // Process PDFs
    const pdfContainer = module.querySelector('.pdf-files-container');
    if (pdfContainer) {
      const pdfInputs = pdfContainer.querySelectorAll('input[type="file"]');
      let pdfCount = 0;
      
      pdfInputs.forEach((input, idx) => {
        if (input.files.length > 0) {
          pdfCount++;
          formData.append(`module_${moduleIndex}_pdf_${pdfCount}`, input.files[0]);
          
          // Get the file name display if it exists
          const fileNameSpan = input.parentElement.nextElementSibling;
          if (fileNameSpan && fileNameSpan.classList.contains('selected-file-name')) {
            formData.append(`module_${moduleIndex}_pdf_${pdfCount}_title`, input.files[0].name);
          }
        }
      });
      formData.append(`module_${moduleIndex}_pdf_count`, pdfCount);
    }
    
    // Process Videos
    const videoContainer = module.querySelector('.videos-container');
    if (videoContainer) {
      const videoItems = videoContainer.querySelectorAll('.video-item');
      let videoCount = 0;
      
      videoItems.forEach((item, idx) => {
        const videoInput = item.querySelector('input[type="file"]');
        const videoTitleInput = item.querySelector('input[type="text"]');
        
        if (videoInput && videoInput.files.length > 0) {
          videoCount++;
          formData.append(`module_${moduleIndex}_video_${videoCount}`, videoInput.files[0]);
          
          if (videoTitleInput && videoTitleInput.value) {
            formData.append(`module_${moduleIndex}_video_${videoCount}_title`, videoTitleInput.value);
          } else {
            formData.append(`module_${moduleIndex}_video_${videoCount}_title`, videoInput.files[0].name);
          }
        }
      });
      formData.append(`module_${moduleIndex}_video_count`, videoCount);
    }
    
    // Process Materials
    const materialsContainer = module.querySelector('.materials-container');
    if (materialsContainer) {
      const materialInputs = materialsContainer.querySelectorAll('input[type="file"]');
      let materialCount = 0;
      
      materialInputs.forEach((input, idx) => {
        if (input.files.length > 0) {
          materialCount++;
          formData.append(`module_${moduleIndex}_material_${materialCount}`, input.files[0]);
          formData.append(`module_${moduleIndex}_material_${materialCount}_title`, input.files[0].name);
        }
      });
      formData.append(`module_${moduleIndex}_material_count`, materialCount);
    }
    
    // Process Notes
    const notesContainer = module.querySelector('.notes-container');
    if (notesContainer) {
      const noteInputs = notesContainer.querySelectorAll('input[type="text"]');
      let noteCount = 0;
      
      noteInputs.forEach((input, idx) => {
        if (input.value.trim()) {
          noteCount++;
          formData.append(`module_${moduleIndex}_note_${noteCount}`, input.value.trim());
        }
      });
      formData.append(`module_${moduleIndex}_note_count`, noteCount);
    }

    // Process quiz data
    const quizToggle = module.querySelector('.quiz-toggle');
    if (quizToggle && quizToggle.checked) {
      formData.append(`module_${moduleIndex}_has_quiz`, '1');
      console.log('Module has quiz:', moduleIndex);

      const questionsContainer = module.querySelector('.questions-container');
      if (questionsContainer) {
        const questions = questionsContainer.querySelectorAll('.question-card:not([style*="display: none"])');
        formData.append(`module_${moduleIndex}_question_count`, questions.length);
        console.log('Found questions:', questions.length);

        questions.forEach((question, questionIndex) => {
          const questionNumber = questionIndex + 1;
          const questionType = question.querySelector('.question-type-select').value;
          const questionText = question.querySelector('input[name^="question_text"]').value;

          if (!questionText.trim()) {
            console.error('Empty question text:', { moduleIndex, questionNumber });
            return;
          }

          formData.append(`module_${moduleIndex}_question_${questionNumber}_type`, questionType);
          formData.append(`module_${moduleIndex}_question_${questionNumber}_text`, questionText);

          console.log('Processing question:', { moduleIndex, questionNumber, type: questionType });

          if (questionType === 'multiple_choice') {
            const answerItems = question.querySelectorAll('.answer-item:not([style*="display: none"])');
            const answerCount = answerItems.length;
            formData.append(`module_${moduleIndex}_question_${questionNumber}_answer_count`, answerCount);

            let correctAnswerIndex = -1;
            let hasEmptyAnswer = false;

            answerItems.forEach((item, answerIndex) => {
              const radio = item.querySelector('input[type="radio"]');
              const textInput = item.querySelector('input[type="text"]');
              const answerText = textInput.value.trim();

              if (!answerText) {
                hasEmptyAnswer = true;
                console.error('Empty answer text:', { moduleIndex, questionNumber, answerIndex: answerIndex + 1 });
                return;
              }

              if (radio.checked) {
                correctAnswerIndex = answerIndex;
              }

              formData.append(
                `module_${moduleIndex}_question_${questionNumber}_answer_${answerIndex + 1}`, 
                answerText
              );
            });

            if (correctAnswerIndex === -1) {
              console.error('No correct answer selected:', { moduleIndex, questionNumber });
              showAlert('danger', 'يجب تحديد الإجابة الصحيحة لجميع الأسئلة');
              submitBtn.disabled = false;
              submitBtn.innerHTML = originalText;
              isValid = false;
              return;
            }

            if (hasEmptyAnswer) {
              showAlert('danger', 'يجب ملء جميع الإجابات');
              submitBtn.disabled = false;
              submitBtn.innerHTML = originalText;
              isValid = false;
              return;
            }

            formData.append(
              `module_${moduleIndex}_question_${questionNumber}_correct_answer`,
              (correctAnswerIndex + 1).toString()
            );
          } 
          else if (questionType === 'true_false') {
            const trueRadio = question.querySelector('input[value="true"]');
            const falseRadio = question.querySelector('input[value="false"]');
            
            if (!trueRadio || !falseRadio || (!trueRadio.checked && !falseRadio.checked)) {
              console.error('No true/false option selected or elements not found:', { moduleIndex, questionNumber });
              showAlert('danger', 'يجب اختيار إجابة صحيحة (صح أو خطأ)');
              submitBtn.disabled = false;
              submitBtn.innerHTML = originalText;
              isValid = false;
              return;
            }
            
            const correctAnswer = trueRadio.checked ? 'true' : 'false';
            formData.append(`module_${moduleIndex}_question_${questionNumber}_correct_answer`, correctAnswer);
          } 
          else if (questionType === 'short_answer') {
            const answerInput = question.querySelector('input[name^="answer_short_"]');
            
            if (!answerInput) {
              console.error('Short answer input not found:', { moduleIndex, questionNumber });
              showAlert('danger', 'حدث خطأ في العثور على حقل الإجابة القصيرة');
              submitBtn.disabled = false;
              submitBtn.innerHTML = originalText;
              isValid = false;
              return;
            }
            
            const correctAnswer = answerInput.value.trim();
            
            if (!correctAnswer) {
              console.error('Empty short answer found:', { moduleIndex, questionNumber });
              showAlert('danger', 'يجب إدخال الإجابة الصحيحة للسؤال القصير');
              submitBtn.disabled = false;
              submitBtn.innerHTML = originalText;
              isValid = false;
              return;
            }
            
            formData.append(`module_${moduleIndex}_question_${questionNumber}_correct_answer`, correctAnswer);
          }
        });
      }
    } else {
      console.log('Module has no quiz:', moduleId);
    }
  });

  if (!isValid) {
    submitBtn.innerHTML = originalText;
    submitBtn.disabled = false;
    showAlert('danger', 'يوجد أخطاء في النموذج. يرجى مراجعة البيانات المدخلة.');
    return;
  }

  // Get the form element
  const form = document.getElementById('course-form');
  
  // Submit via fetch
  fetch(form.action, {
    method: 'POST',
    body: formData,
    headers: {
      'X-Requested-With': 'XMLHttpRequest',
      'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
    }
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      showAlert('success', data.message);
      setTimeout(() => {
        if (data.redirect_url) {
          window.location.href = data.redirect_url;
        }
      }, 2000);
    } else {
      showAlert('danger', data.message);
      submitBtn.innerHTML = originalText;
      submitBtn.disabled = false;
    }
  })
  .catch(error => {
    console.error('Error:', error);
    showAlert('danger', 'حدث خطأ في الشبكة');
    submitBtn.innerHTML = originalText;
    submitBtn.disabled = false;
  });
}

function validateForm() {
  // Simple validation for required fields
  const requiredFields = document.querySelectorAll('[required]');
  
  let isValid = true;
  requiredFields.forEach(field => {
    // Skip hidden fields
    if (field.offsetParent === null) {
      return;
    }
    
    if (!field.value) {
      field.classList.add('is-invalid');
      isValid = false;
    } else {
      field.classList.remove('is-invalid');
    }
  });
  
  // Validate modules
  const modules = document.querySelectorAll('.module-card:not([style*="display: none"])');
  if (modules.length === 0) {
    showAlert('danger', 'يجب إضافة موديول واحد على الأقل');
    return false;
  }
  
  // Validate each module has either video names or PDF files
  let hasContentError = false;
  modules.forEach(module => {
    const videoNames = module.querySelectorAll('.video-names-container input[type="text"]');
    const pdfFiles = module.querySelectorAll('.pdf-files-container input[type="file"]');
    let hasContent = false;
    
    // Check video names
    videoNames.forEach(input => {
      if (input.value.trim()) {
        hasContent = true;
      }
    });
    
    // Check PDF files
    pdfFiles.forEach(input => {
      if (input.files && input.files.length > 0) {
        hasContent = true;
      }
    });
    
    if (!hasContent) {
      hasContentError = true;
    }
  });
  
  if (hasContentError) {
    showAlert('danger', 'يجب إضافة فيديو أو ملف PDF على الأقل لكل موديول');
    return false;
  }
  
  // Add validation for quiz questions if needed
  const quizToggles = document.querySelectorAll('.quiz-toggle:checked');
  quizToggles.forEach(toggle => {
    const moduleElement = toggle.closest('.module-card');
    const questions = moduleElement.querySelectorAll('.question-card:not([style*="display: none"])');
    
    if (questions.length === 0) {
      showAlert('danger', 'يجب إضافة سؤال واحد على الأقل للاختبار');
      isValid = false;
      return;
    }
    
    // Validate questions
    questions.forEach(question => {
      const questionText = question.querySelector('input[name^="question_text"]');
      if (!questionText || !questionText.value.trim()) {
        showAlert('danger', 'يجب ملء نص السؤال لجميع الأسئلة');
        isValid = false;
        return;
      }
      
      const questionType = question.querySelector('.question-type-select').value;
      
      if (questionType === 'multiple_choice') {
        const answers = question.querySelectorAll('.answer-item:not([style*="display: none"])');
        if (answers.length < 2) {
          showAlert('danger', 'يجب إضافة إجابتين على الأقل لكل سؤال اختيار متعدد');
          isValid = false;
          return;
        }
        
        let hasCorrectAnswer = false;
        let hasEmptyAnswer = false;
        
        answers.forEach(answer => {
          const radio = answer.querySelector('input[type="radio"]');
          const text = answer.querySelector('input[type="text"]');
          
          if (!text || !text.value.trim()) {
            hasEmptyAnswer = true;
            return;
          }
          
          if (radio && radio.checked) {
            hasCorrectAnswer = true;
          }
        });
        
        if (hasEmptyAnswer) {
          showAlert('danger', 'يجب ملء جميع الإجابات');
          isValid = false;
          return;
        }
        
        if (!hasCorrectAnswer) {
          showAlert('danger', 'يجب تحديد الإجابة الصحيحة لكل سؤال');
          isValid = false;
          return;
        }
      } 
      else if (questionType === 'true_false') {
        const trueRadio = question.querySelector('input[value="true"]');
        const falseRadio = question.querySelector('input[value="false"]');
        
        if ((!trueRadio || !falseRadio) || (!trueRadio.checked && !falseRadio.checked)) {
          showAlert('danger', 'يجب اختيار صح أو خطأ لكل سؤال');
          isValid = false;
          return;
        }
      } 
      else if (questionType === 'short_answer') {
        const answerContainer = question.querySelector('.short-answer-container');
        const answer = answerContainer ? answerContainer.querySelector('input[type="text"]') : null;
        
        if (!answer || !answer.value || !answer.value.trim()) {
          showAlert('danger', 'يجب إدخال الإجابة الصحيحة لكل سؤال من نوع إجابة قصيرة');
          isValid = false;
          return;
        }
      }
    });
  });
  
  return isValid;
};

// Function to show Bootstrap alerts
function showAlert(type, message) {
  // Check if alerts container exists, if not create it
  let alertsContainer = document.getElementById('alerts-container');
  if (!alertsContainer) {
    alertsContainer = document.createElement('div');
    alertsContainer.id = 'alerts-container';
    alertsContainer.className = 'position-fixed top-0 end-0 p-3';
    alertsContainer.style.zIndex = '1050';
    document.body.appendChild(alertsContainer);
  }
  
  const alertDiv = document.createElement('div');
  alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
  alertDiv.role = 'alert';
  alertDiv.innerHTML = `
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
  `;
  
  alertsContainer.appendChild(alertDiv);
  
  // Auto-dismiss after 5 seconds
  setTimeout(() => {
    alertDiv.classList.remove('show');
    setTimeout(() => {
      alertDiv.remove();
    }, 300);
  }, 5000);
};

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
  // Add event listener to the "Add Module" button
  const addModuleBtn = document.getElementById('add-module-btn');
  if (addModuleBtn) {
    addModuleBtn.addEventListener('click', addModule);
  }
  
  // Add event listener to the submit button
  const submitBtn = document.getElementById('submit-course-btn');
  if (submitBtn) {
    submitBtn.addEventListener('click', function(e) {
      e.preventDefault();
      submitCourse();
    });
  }

  // Initialize existing modules
  initExistingModules();
  
  // Initialize PDF delete checkboxes
  const pdfDeleteCheckboxes = document.querySelectorAll('input[name^="delete_"]');
  pdfDeleteCheckboxes.forEach(checkbox => {
    checkbox.addEventListener('change', function() {
      // If checkbox is checked, add a visual indication
      const parentElement = this.closest('.d-flex');
      if (parentElement) {
        if (this.checked) {
          parentElement.classList.add('bg-danger', 'bg-opacity-10');
        } else {
          parentElement.classList.remove('bg-danger', 'bg-opacity-10');
        }
      }
    });
  });
});

// Add a function to update question numbering
const updateQuestionNumbering = function(questionsContainer) {
  const visibleQuestions = Array.from(questionsContainer.querySelectorAll('.question-card'))
    .filter(q => q.style.display !== 'none');
  
  visibleQuestions.forEach((question, index) => {
    const questionHeader = question.querySelector('h6');
    if (questionHeader) {
      questionHeader.textContent = `سؤال #${index + 1}`;
    }
  });
};

// Function to initialize event listeners for existing modules
const initExistingModules = function() {
  // Setup event listeners for existing modules
  const existingModules = document.querySelectorAll('.module-card[id^="existing_module_"]');
  
  existingModules.forEach(moduleElement => {
    const moduleId = moduleElement.id;
    
    // Setup module event listeners
    setupModuleEventListeners(moduleElement, moduleId);
    
    // Setup quiz toggle
    const quizToggle = moduleElement.querySelector('.quiz-toggle');
    if (quizToggle) {
      quizToggle.addEventListener('change', function() {
        toggleQuiz(moduleElement, this.checked);
      });
      
      // Initialize quiz section visibility
      const quizSection = moduleElement.querySelector('.quiz-section');
      if (quizSection) {
        quizSection.style.display = quizToggle.checked ? 'block' : 'none';
      }
    }
    
    // Setup add note button
    const addNoteBtn = moduleElement.querySelector('.add-note-btn');
    if (addNoteBtn) {
      addNoteBtn.addEventListener('click', function() {
        const moduleIdAttr = this.getAttribute('data-module-id');
        addNote(moduleElement, moduleIdAttr || moduleId);
      });
    }
    
    // Setup remove note buttons
    const removeNoteBtns = moduleElement.querySelectorAll('.remove-note-btn');
    removeNoteBtns.forEach(btn => {
      btn.addEventListener('click', function() {
        removeNote(this);
      });
    });
    
    // Setup add video name button
    const addVideoNameBtn = moduleElement.querySelector('.add-video-name-btn');
    if (addVideoNameBtn) {
      addVideoNameBtn.addEventListener('click', function() {
        const moduleIdAttr = this.getAttribute('data-module-id');
        addVideoName(moduleElement, moduleIdAttr || moduleId);
      });
    }
    
    // Setup remove video name buttons
    const removeVideoNameBtns = moduleElement.querySelectorAll('.remove-video-name-btn');
    removeVideoNameBtns.forEach(btn => {
      btn.addEventListener('click', function() {
        removeVideoName(this);
      });
    });
    
    // Setup add question button
    const addQuestionBtn = moduleElement.querySelector('.add-question-btn');
    if (addQuestionBtn) {
      addQuestionBtn.addEventListener('click', function() {
        const moduleIdAttr = this.getAttribute('data-module-id');
        addQuestion(moduleElement, moduleIdAttr || moduleId);
      });
    }
    
    // Setup existing questions
    const existingQuestions = moduleElement.querySelectorAll('.question-card');
    existingQuestions.forEach(questionElement => {
      const questionId = questionElement.id.replace('existing_question_', '');
      setupQuestionEventListeners(questionElement, moduleElement, moduleId, questionId);
      
      // Setup add answer button
      const addAnswerBtn = questionElement.querySelector('.add-answer-btn');
      if (addAnswerBtn) {
        addAnswerBtn.addEventListener('click', function() {
          addAnswer(questionElement, moduleId, questionId);
        });
      }
      
      // Setup remove answer buttons
      const removeAnswerBtns = questionElement.querySelectorAll('.remove-answer-btn');
      removeAnswerBtns.forEach(btn => {
        btn.addEventListener('click', function() {
          const answersContainer = questionElement.querySelector('.answers-container');
          removeAnswer(this, answersContainer);
        });
      });
    });
  });
};

// PDF functions
function addPdf(moduleElement, moduleId) {
  const pdfContainer = moduleElement.querySelector('.pdf-files-container');
  const moduleNumber = moduleElement.id.replace('module_', '');
  
  const inputGroup = document.createElement('div');
  inputGroup.className = 'input-group mb-2';
  
  const fileInput = document.createElement('input');
  fileInput.type = 'file';
  fileInput.className = 'form-control';
  fileInput.name = `module_${moduleNumber}_pdf[]`;
  fileInput.accept = '.pdf';
  fileInput.required = false;
  
  // Add file change event listener to show file name
  fileInput.addEventListener('change', function() {
    if (this.files.length > 0) {
      const fileNameSpan = document.createElement('span');
      fileNameSpan.className = 'selected-file-name mt-1 mb-2 text-primary';
      fileNameSpan.style.display = 'block';
      fileNameSpan.innerHTML = `<i class="fas fa-file-pdf me-1"></i>${this.files[0].name}`;
      
      // Remove any existing file name display
      const existingFileName = inputGroup.nextElementSibling;
      if (existingFileName && existingFileName.classList.contains('selected-file-name')) {
        existingFileName.remove();
      }
      
      // Add file name after input group
      inputGroup.insertAdjacentElement('afterend', fileNameSpan);
    }
  });
  
  const removeButton = document.createElement('button');
  removeButton.type = 'button';
  removeButton.className = 'btn btn-outline-danger remove-pdf-btn';
  removeButton.innerHTML = '<i class="fas fa-times"></i>';
  
  inputGroup.appendChild(fileInput);
  inputGroup.appendChild(removeButton);
  pdfContainer.appendChild(inputGroup);
  
  // Add event listener to the new remove button
  removeButton.addEventListener('click', () => {
    // Also remove any file name display
    const fileNameSpan = inputGroup.nextElementSibling;
    if (fileNameSpan && fileNameSpan.classList.contains('selected-file-name')) {
      fileNameSpan.remove();
    }
    inputGroup.remove();
  });
}

// Additional materials functions
function addMaterial(moduleElement, moduleId) {
  const materialsContainer = moduleElement.querySelector('.materials-container');
  const moduleNumber = moduleElement.id.replace('module_', '');
  
  const inputGroup = document.createElement('div');
  inputGroup.className = 'input-group mb-2';
  
  const fileInput = document.createElement('input');
  fileInput.type = 'file';
  fileInput.className = 'form-control';
  fileInput.name = `module_${moduleNumber}_materials[]`;
  
  const removeButton = document.createElement('button');
  removeButton.type = 'button';
  removeButton.className = 'btn btn-outline-danger';
  removeButton.innerHTML = '<i class="fas fa-times"></i>';
  removeButton.onclick = function() {
    inputGroup.remove();
  };
  
  inputGroup.appendChild(fileInput);
  inputGroup.appendChild(removeButton);
  materialsContainer.appendChild(inputGroup);
}

// These functions are available globally in the browser
// No need to export them as this is browser JavaScript
