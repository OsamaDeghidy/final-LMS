// Global variables
let currentStep = 0;
let moduleCount = 0;
let questionCounter = 0;
const MAX_ANSWERS = 5;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  // Add module button
  const addModuleBtn = document.getElementById('add-module-btn');
  if (addModuleBtn) {
    addModuleBtn.addEventListener('click', addModule);
  }
  
  // Add initial module if none exists
  const modulesContainer = document.getElementById('modules-container');
  if (modulesContainer && modulesContainer.children.length === 0) {
    addModule();
  }
  
  // Handle form submission
  const form = document.getElementById('course-form');
  const submitBtn = document.getElementById('submit-course-btn');
  
  if (form && submitBtn) {
    form.addEventListener('submit', function(e) {
      e.preventDefault();
      submitCourse();
    });
    
    submitBtn.addEventListener('click', function(e) {
      e.preventDefault();
      submitCourse();
    });
  }
});



// Show alert message
function showAlert(type, message) {
  const alertsContainer = document.getElementById('alerts-container');
  
  // Create alert element
  const alertDiv = document.createElement('div');
  alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
  alertDiv.role = 'alert';
  alertDir = document.dir;
  
  // Set the alert content
  alertDiv.innerHTML = `
    <div class="d-flex align-items-center">
      <i class="fas ${type === 'danger' ? 'fa-exclamation-circle' : 'fa-check-circle'} me-2"></i>
      <div>${message}</div>
    </div>
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
  `;
  
  // Add the alert to the container
  alertsContainer.appendChild(alertDiv);
  
  // Auto-dismiss after 5 seconds
  setTimeout(() => {
    const alert = bootstrap.Alert.getOrCreateInstance(alertDiv);
    if (alert) {
      alert.close();
    }
  }, 5000);
}

// Navigation functions
function goToNextStep() {
  if (!validateCurrentStep()) {
    return false;
  }
  
  const steps = document.querySelectorAll('#stepper .step-item');
  const stepCards = document.querySelectorAll('.step-card');
  
  if (currentStep < steps.length - 1) {
    // Hide current step
    stepCards[currentStep].classList.add('d-none');
    steps[currentStep].classList.remove('active');
    
    // Show next step
    currentStep++;
    stepCards[currentStep].classList.remove('d-none');
    steps[currentStep].classList.add('active');
    
    // If moving to review step, update the summary
    if (currentStep === 2) {
      updateCourseSummary();
    }
  }
  
  return true;
}

function nextStep() {
  // Validate current step before proceeding
  if (validateCurrentStep()) {
    // If moving to the review step (step 3), update the summary
    if (currentStep === 1) {
      updateCourseSummary();
    }
    goToNextStep();
  }
}

// Function to update the course summary in the review step
function updateCourseSummary() {
  const title = document.querySelector('input[name="name"]').value;
  const smallDesc = document.querySelector('input[name="small_description"]').value;
  const price = document.querySelector('input[name="price"]').value;
  const level = document.querySelector('select[name="level"]').value;
  const modules = document.querySelectorAll('.module-card:not([style*="display: none"])').length;
  
  // Update summary elements
  document.getElementById('summary-title').textContent = title || 'غير محدد';
  document.getElementById('summary-small-desc').textContent = smallDesc || 'غير محدد';
  document.getElementById('summary-price').textContent = price ? `$${price}` : 'غير محدد';
  
  let levelText = 'غير محدد';
  if (level === 'beginner') levelText = 'مبتدئ';
  else if (level === 'intermediate') levelText = 'متوسط';
  else if (level === 'advanced') levelText = 'متقدم';
  
  document.getElementById('summary-level').textContent = levelText;
  document.getElementById('summary-modules').textContent = modules;
}

function prevStep() {
  const steps = document.querySelectorAll('#stepper .step-item');
  const stepCards = document.querySelectorAll('.step-card');
  
  if (currentStep > 0) {
    // Hide current step
    stepCards[currentStep].classList.add('d-none');
    steps[currentStep].classList.remove('active');
    
    // Show previous step
    currentStep--;
    stepCards[currentStep].classList.remove('d-none');
    steps[currentStep].classList.add('active');
  }
}

function validateCurrentStep() {
  // Simple validation for required fields
  const currentStepCard = document.querySelectorAll('.step-card')[currentStep];
  const requiredFields = currentStepCard.querySelectorAll('[required]');
  
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
  
  if (!isValid) {
    showAlert('danger', 'يرجى ملء جميع الحقول المطلوبة');
  }
  
  // If we're on step 2 (modules), check if at least one module exists
  if (currentStep === 1) {
    const modules = document.querySelectorAll('.module-card:not([style*="display: none"])');
    if (modules.length === 0) {
      showAlert('danger', 'يجب إضافة موديول واحد على الأقل');
      return false;
    }
  }
  
  return isValid;
}

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

  // Update module title
  const titleElement = moduleElement.querySelector('.card-header h5');
  if (titleElement) {
    titleElement.innerHTML = `<i class="fas fa-layer-group text-primary me-2"></i>الموديول ${moduleCount}`;
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

  // Add PDF button
  const addPdfBtn = moduleElement.querySelector('.add-pdf-btn');
  if (addPdfBtn) {
    addPdfBtn.addEventListener('click', () => addPdf(moduleElement, moduleId));
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
  const addQuestionBtn = moduleElement.querySelector('.add-question-btn');
  if (addQuestionBtn) {
    addQuestionBtn.setAttribute('data-module-id', moduleId);
    addQuestionBtn.addEventListener('click', () => addQuestion(moduleElement, moduleId));
  } else {
    console.error('Add question button not found in module:', moduleId);
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
  }
}

// Question and Answer functions
function addQuestion(moduleElement) {
  questionCounter++;
  const questionId = `question_${questionCounter}`;
  
  const template = document.getElementById('question-template');
  if (!template) {
    console.error('Question template not found');
    return;
  }
  
  const questionElement = template.content.cloneNode(true);
  const questionCard = questionElement.querySelector('.question-card');
  questionCard.dataset.questionId = questionId;
  
  // Find the questions container in the module
  const questionsContainer = moduleElement.querySelector('.questions-container');
  if (!questionsContainer) {
    console.error('Questions container not found');
    return;
  }
  
  questionsContainer.appendChild(questionElement);
  
  // Initialize question type
  updateQuestionType(questionCard.querySelector('.question-type'));
  
  return questionCard;
}

function updateQuestionType(selectElement) {
  const questionCard = selectElement.closest('.question-card');
  const answersContainer = questionCard.querySelector('.answers-container');
  const questionType = selectElement.value;
  
  // Clear existing answers
  answersContainer.innerHTML = '';
  
  if (questionType === 'true_false') {
    // Add true/false options
    const trueFalseTemplate = `
      <div class="answer-group mb-2">
        <div class="form-check">
          <input class="form-check-input" type="radio" name="question_${questionCounter}_correct" value="true" required>
          <label class="form-check-label">
            صح
          </label>
        </div>
      </div>
      <div class="answer-group mb-2">
        <div class="form-check">
          <input class="form-check-input" type="radio" name="question_${questionCounter}_correct" value="false" required>
          <label class="form-check-label">
            خطأ
          </label>
        </div>
      </div>
    `;
    answersContainer.innerHTML = trueFalseTemplate;
  } 
  else if (questionType === 'short_answer') {
    // Add short answer field
    const shortAnswerTemplate = `
      <div class="mb-3">
        <input type="text" class="form-control" name="question_${questionCounter}_answer" required>
        <input type="hidden" name="question_${questionCounter}_type" value="short_answer">
      </div>
    `;
    answersContainer.innerHTML = shortAnswerTemplate;
  } 
  else {
    // Default to multiple choice
    const mcqTemplate = `
      <div class="answer-group mb-2">
        <div class="input-group">
          <div class="input-group-text">
            <input type="radio" name="question_${questionCounter}_correct" value="0" required>
          </div>
          <input type="text" class="form-control" name="question_${questionCounter}_answer[]" required placeholder="الإجابة">
          <button type="button" class="btn btn-outline-danger remove-answer" onclick="removeAnswer(this, this.closest('.answer-group'))">
            <i class="fas fa-times"></i>
          </button>
        </div>
      </div>
      <div class="answer-group mb-2">
        <div class="input-group">
          <div class="input-group-text">
            <input type="radio" name="question_${questionCounter}_correct" value="1" required>
          </div>
          <input type="text" class="form-control" name="question_${questionCounter}_answer[]" required placeholder="الإجابة">
          <button type="button" class="btn btn-outline-danger remove-answer" onclick="removeAnswer(this, this.closest('.answer-group'))">
            <i class="fas fa-times"></i>
          </button>
        </div>
      </div>
      <button type="button" class="btn btn-sm btn-outline-primary add-answer-btn mt-2" 
              onclick="addAnswer(this.closest('.question-card'), '${questionCounter}')">
        <i class="fas fa-plus me-1"></i>إضافة إجابة
      </button>
      <input type="hidden" name="question_${questionCounter}_type" value="mcq">
    `;
    answersContainer.innerHTML = mcqTemplate;
  }
}

function addAnswer(questionElement, questionId) {
  const answersContainer = questionElement.querySelector('.answers-container');
  const answerGroups = answersContainer.querySelectorAll('.answer-group');
  const answerCount = answerGroups.length;
  
  // Check if we've reached the maximum number of answers
  if (answerCount >= MAX_ANSWERS) {
    showAlert('warning', `لا يمكن إضافة أكثر من ${MAX_ANSWERS} إجابات`);
    return;
  }
  
  const answerGroup = document.createElement('div');
  answerGroup.className = 'answer-group mb-2';
  answerGroup.innerHTML = `
    <div class="input-group">
      <div class="input-group-text">
        <input type="radio" name="question_${questionId}_correct" value="${answerCount}" required>
      </div>
      <input type="text" class="form-control" name="question_${questionId}_answer[]" required placeholder="الإجابة">
      <button type="button" class="btn btn-outline-danger remove-answer" onclick="removeAnswer(this, this.closest('.answer-group'))">
        <i class="fas fa-times"></i>
      </button>
    </div>
  `;
  
  // Insert before the add answer button
  const addButton = answersContainer.querySelector('.add-answer-btn');
  if (addButton) {
    answersContainer.insertBefore(answerGroup, addButton);
  } else {
    answersContainer.appendChild(answerGroup);
  }
  
  // If this is the first answer, check it by default
  if (answerCount === 0) {
    const radioInput = answerGroup.querySelector('input[type="radio"]');
    if (radioInput) {
      radioInput.checked = true;
    }
  }
  
  // Focus the new answer input
  const newInput = answerGroup.querySelector('input[type="text"]');
  if (newInput) {
    newInput.focus();
  }
}

function removeAnswer(button, answerElement) {
  const answersContainer = answerElement.parentElement;
  const answerGroups = answersContainer.querySelectorAll('.answer-group');
  
  // Don't allow removing if we're down to 2 answers
  if (answerGroups.length <= 2) {
    showAlert('warning', 'يجب أن يحتوي السؤال على إجابتين على الأقل');
    return;
  }
  
  // Check if we're removing the currently selected answer
  const selectedRadio = answerElement.querySelector('input[type="radio"]:checked');
  
  answerElement.remove();
  
  // Update radio button values and ensure one is checked
  const questionElement = answersContainer.closest('.question-card');
  if (questionElement) {
    const radioButtons = answersContainer.querySelectorAll('input[type="radio"]');
    let hasChecked = false;
    
    radioButtons.forEach((radio, index) => {
      radio.value = index;
      
      // If we removed the selected answer, select the first one
      if (selectedRadio && !hasChecked) {
        radio.checked = true;
        hasChecked = true;
      }
    });
    
    // If no radio is checked (shouldn't happen), check the first one
    if (!hasChecked && radioButtons.length > 0) {
      radioButtons[0].checked = true;
    }
  }
}

function removeQuestion(questionElement) {
  questionElement.remove();
}

function toggleQuiz(moduleElement, isChecked) {
  const quizSection = moduleElement.querySelector('.quiz-section');
  if (!quizSection) return;
  
  if (isChecked) {
    quizSection.style.display = 'block';
  } else {
    quizSection.style.display = 'none';
  }
}

// Submit the course form
function submitCourse() {
  if (!validateForm()) {
    showAlert('danger', 'يرجى ملء جميع الحقول المطلوبة قبل الحفظ');
    return;
  }

  const form = document.getElementById('course-form');
  const formData = new FormData(form);
  const submitBtn = document.getElementById('submit-course-btn');
  const originalText = submitBtn.innerHTML;
  submitBtn.disabled = true;
  let isValid = true;

  // Show loading state
  submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>جاري الحفظ...';
  
  // Add CSRF token
  const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
  
  // Add course image to form data if exists
  const courseImageInput = document.querySelector('input[name="course_image"]');
  if (courseImageInput && courseImageInput.files.length > 0) {
    formData.append('course_image', courseImageInput.files[0]);
  }

  // Add course description and other fields
  formData.append('name', document.querySelector('input[name="name"]').value);
  formData.append('description', document.querySelector('textarea[name="description"]').value);
  formData.append('small_description', document.querySelector('input[name="small_description"]').value);
  formData.append('price', document.querySelector('input[name="price"]').value);
  formData.append('category', document.querySelector('select[name="category"]').value);
  formData.append('level', document.querySelector('select[name="level"]').value);

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
  formData.append('module_count', modules.length);

  modules.forEach(module => {
    if (module.style.display === 'none') return; // Skip hidden modules

    moduleIndex++;
    const moduleId = module.id;
    
    // Process module title and description
    const titleInput = module.querySelector('input[name^="module_title"]');
    const descriptionInput = module.querySelector('textarea[name^="module_description"]');
    
    if (titleInput && descriptionInput) {
      formData.append(`module_${moduleIndex}_title`, titleInput.value);
      formData.append(`module_${moduleIndex}_description`, descriptionInput.value);
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
        }
      });
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
          formData.append(`module_${moduleIndex}_video`, videoInput.files[0]);
          
          if (videoTitleInput && videoTitleInput.value) {
            formData.append(`module_${moduleIndex}_video_title`, videoTitleInput.value);
          }
        }
      });
    }
    
    // Process Notes
    const noteInput = module.querySelector('textarea[name^="module_note"]');
    if (noteInput && noteInput.value) {
      formData.append(`module_${moduleIndex}_note`, noteInput.value);
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
    const quizToggleElement = module.querySelector('.quiz-toggle');
    if (quizToggleElement && quizToggleElement.checked) {
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
