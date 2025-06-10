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
  
  // Set up file input change listeners for PDF files
  document.body.addEventListener('change', function(e) {
    // Handle PDF file input changes
    if (e.target.matches('input[type="file"][accept=".pdf"]')) {
      const pdfInput = e.target;
      if (pdfInput.files.length > 0) {
        const fileName = pdfInput.files[0].name;
        
        // Find the title input in the same card
        const moduleCard = pdfInput.closest('.module-card');
        if (moduleCard) {
          const titleInput = moduleCard.querySelector('.pdf-title');
          if (titleInput && !titleInput.value) {
            // Auto-populate the title field with the filename (without extension)
            titleInput.value = fileName.replace(/\.pdf$/i, '');
          }
          
          // Show file name
          const fileNameSpan = document.createElement('span');
          fileNameSpan.className = 'selected-file-name mt-1 mb-2 text-primary';
          fileNameSpan.style.display = 'block';
          fileNameSpan.innerHTML = `<i class="fas fa-file-pdf me-1"></i>${fileName}`;
          
          // Remove any existing file name display
          const existingFileName = pdfInput.nextElementSibling;
          if (existingFileName && existingFileName.classList.contains('selected-file-name')) {
            existingFileName.remove();
          }
          
          // Add file name after input
          pdfInput.insertAdjacentElement('afterend', fileNameSpan);
        }
      }
    }
  });
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
  let isValid = true;
  const currentStepCard = document.querySelectorAll('.step-card')[currentStep];
  const requiredFields = currentStepCard.querySelectorAll('[required]');
  let errors = [];
  
  // Check required text fields
  requiredFields.forEach(field => {
    // Skip hidden fields
    if (field.offsetParent === null) {
      return;
    }
    
    if (!field.value.trim()) {
      field.classList.add('is-invalid');
      isValid = false;
    } else {
      field.classList.remove('is-invalid');
    }
  });

  // If we're on step 2 (modules), validate module content
  if (currentStep === 1) {
    const modules = document.querySelectorAll('.module-card:not([style*="display: none"])');
    
    if (modules.length === 0) {
      isValid = false;
      showAlert('danger', 'يجب إضافة موديول واحد على الأقل');
      return false;
    }

    // Validate each module
    modules.forEach((module, index) => {
      const moduleNum = index + 1;
      
      // Check module title
      const titleInput = module.querySelector('input[name^="module_name"]');
      if (!titleInput || !titleInput.value.trim()) {
        isValid = false;
        showAlert('danger', `يرجى إدخال عنوان للموديول ${moduleNum}`);
      }

      // Check video file
      const videoInput = module.querySelector('input[name^="module_video"]');
      if (!videoInput || !videoInput.files || videoInput.files.length === 0) {
        isValid = false;
        showAlert('danger', `يجب إضافة فيديو للموديول ${moduleNum}`);
      }

      // Check video title
      const videoTitleInput = module.querySelector('input[name^="video_title"]');
      if (!videoTitleInput || !videoTitleInput.value.trim()) {
        isValid = false;
        showAlert('danger', `يرجى إدخال عنوان الفيديو للموديول ${moduleNum}`);
      }

      // Check PDF file
      const pdfInput = module.querySelector('input[name^="module_pdf"]');
      if (!pdfInput || !pdfInput.files || pdfInput.files.length === 0) {
        isValid = false;
        showAlert('danger', `يجب إضافة ملف PDF للموديول ${moduleNum}`);
      }
    });
  }

  if (!isValid) {
    showAlert('danger', 'يرجى ملء جميع الحقول المطلوبة');
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

async function submitCourse() {
  // Get form and submit button
  const form = document.getElementById('course-form');
  const submitBtn = document.getElementById('submit-course-btn');
  
  // Validate form
  if (!validateForm()) {
    return false;
  }
  
  // Disable submit button and show loading state
  const originalText = submitBtn.innerHTML;
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> جاري الحفظ...';
  
  try {
    // Create FormData object
    const formData = new FormData(form);
    
    // Add CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    formData.append('csrfmiddlewaretoken', csrfToken);
    
    // Process modules data
    const modules = [];
    const moduleElements = document.querySelectorAll('.module-card');
    
    if (moduleElements.length === 0) {
      showAlert('danger', 'يجب إضافة موديول واحد على الأقل');
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalText;
      return false;
    }
    
    // Process each module
    moduleElements.forEach((moduleElement, index) => {
      const moduleId = moduleElement.id.replace('module_', '');
      const moduleData = {
        id: moduleId,
        name: moduleElement.querySelector('input[name^="module_name"]').value,
        number: index + 1,
        description: moduleElement.querySelector('textarea[name^="module_description"]')?.value || ''
      };
      
      // Process video file
      const videoInput = moduleElement.querySelector('input[type="file"][accept^="video/"]');
      if (videoInput && videoInput.files.length > 0) {
        formData.append(`module_${moduleId}_video`, videoInput.files[0]);
        moduleData.video = videoInput.files[0].name;
        
        // Add video title
        const videoTitleInput = moduleElement.querySelector('input[name^="video_title"]');
        if (videoTitleInput && videoTitleInput.value) {
          formData.append(`video_title_${moduleId}`, videoTitleInput.value);
          moduleData.video_title = videoTitleInput.value;
        }
      }
      
      // Process PDF file
      const pdfInput = moduleElement.querySelector('input[type="file"][accept=".pdf"]');
      if (pdfInput && pdfInput.files.length > 0) {
        // Add the PDF file to form data
        formData.append(`module_${moduleId}_pdf`, pdfInput.files[0]);
        moduleData.pdf = pdfInput.files[0].name;
        
        // Add PDF title if available
        const pdfTitleInput = moduleElement.querySelector('.pdf-title');
        if (pdfTitleInput && pdfTitleInput.value) {
          formData.append(`pdf_title_${moduleId}`, pdfTitleInput.value);
          moduleData.pdf_title = pdfTitleInput.value;
        }
      }
      
      // Process quiz if exists
      const quizToggle = moduleElement.querySelector('.quiz-toggle');
      if (quizToggle && quizToggle.checked) {
        const questions = [];
        const questionElements = moduleElement.querySelectorAll('.question-card');
        
        // Add quiz data to moduleData
        moduleData.has_quiz = true;
        
        // Process each question
        questionElements.forEach((questionElement, qIndex) => {
          const questionText = questionElement.querySelector('.question-text')?.value;
          const questionType = questionElement.querySelector('.question-type')?.value || 'mcq';
          
          if (questionText) {
            // Add question text to form data
            formData.append(`module_${moduleId}_question_text[]`, questionText);
            formData.append(`module_${moduleId}_question_type[]`, questionType);
            
            const question = {
              text: questionText,
              question_type: questionType,
              answers: []
            };
            
            // Process answers
            const answerElements = questionElement.querySelectorAll('.answer-item');
            const correctAnswers = [];
            
            answerElements.forEach((answerElement, aIndex) => {
              const answerText = answerElement.querySelector('input[name^="answer_text"]')?.value;
              const isCorrect = answerElement.querySelector('input[type="radio"], input[type="checkbox"]')?.checked || false;
              
              if (answerText) {
                // Add answer text to form data
                formData.append(`module_${moduleId}_question_${qIndex}_answer_text[]`, answerText);
                
                // Track correct answers
                if (isCorrect) {
                  correctAnswers.push(aIndex.toString());
                }
                
                question.answers.push({
                  text: answerText,
                  is_correct: isCorrect
                });
              }
            });
            
            // Add correct answers to form data
            correctAnswers.forEach(index => {
              formData.append(`module_${moduleId}_question_${qIndex}_correct_answer[]`, index);
            });
            
            if (question.answers.length > 0) {
              questions.push(question);
            }
          }
        });
        
        // Add quiz data to moduleData
        moduleData.quiz = {
          title: `اختبار ${moduleData.name}`,
          questions: questions,
          time_limit: 30,
          pass_mark: 50
        };
      }
      
      modules.push(moduleData);
    });
    
    // Add modules data as JSON
    formData.append('modules', JSON.stringify(modules));
    
    // Log form data for debugging
    console.log('=== Form Data ===');
    for (let [key, value] of formData.entries()) {
      if (value instanceof File) {
        console.log(`${key}:`, {
          name: value.name,
          type: value.type,
          size: value.size
        });
      } else if (key === 'modules') {
        console.log('modules:', JSON.parse(value));
      } else {
        console.log(`${key}:`, value);
      }
    }
    
    // Submit the form
    const response = await fetch(form.action, {
      method: 'POST',
      body: formData,
      headers: {
        'X-Requested-With': 'XMLHttpRequest'
      },
      credentials: 'same-origin'
    });
    
    const result = await response.json();
    
    if (response.ok && result.success) {
      showAlert('success', 'تم حفظ الدورة بنجاح! سيتم مراجعتها من قبل الإدارة.');
      setTimeout(() => {
        window.location.href = result.redirect_url || '/my-courses/';
      }, 2000);
    } else {
      throw new Error(result.message || 'حدث خطأ أثناء حفظ الدورة');
    }
  } catch (error) {
    console.error('Error:', error);
    showAlert('danger', error.message || 'حدث خطأ أثناء حفظ الدورة');
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = originalText;
  }




    





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
  
  // Validate each module
  let moduleIndex = 0;
  let hasError = false;
  
  modules.forEach(module => {
    moduleIndex++;
    
    // Check required fields
    const requiredModuleFields = module.querySelectorAll('[required]');
    requiredModuleFields.forEach(field => {
      if (!field.value) {
        field.classList.add('is-invalid');
        hasError = true;
      } else {
        field.classList.remove('is-invalid');
      }
    });
    
    // Check video upload
    const videoInput = module.querySelector('input[name^="module_video"]');
    if (!videoInput || !videoInput.files.length) {
      showAlert('danger', `يجب إضافة فيديو للموديول ${moduleIndex}`);
      hasError = true;
    }
    
    // Check video title
    const videoTitleInput = module.querySelector('input[name^="video_title"]');
    if (!videoTitleInput || !videoTitleInput.value.trim()) {
      showAlert('danger', `يجب إضافة عنوان للفيديو في الموديول ${moduleIndex}`);
      hasError = true;
    }
  });
  
  return !hasError && isValid;
}

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
  
  // Create title input for the PDF
  const titleInput = document.createElement('input');
  titleInput.type = 'text';
  titleInput.className = 'form-control pdf-title';
  titleInput.name = `pdf_title_${moduleNumber}[]`;
  titleInput.placeholder = 'عنوان الملف';
  
  const removeButton = document.createElement('button');
  removeButton.type = 'button';
  removeButton.className = 'btn btn-outline-danger remove-pdf-btn';
  removeButton.innerHTML = '<i class="fas fa-times"></i>';
  
  inputGroup.appendChild(fileInput);
  inputGroup.appendChild(titleInput);
  inputGroup.appendChild(removeButton);
  pdfContainer.appendChild(inputGroup);
  
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
      
      // Auto-populate the title field if it's empty
      if (!titleInput.value) {
        // Remove file extension for the title
        const fileName = this.files[0].name.replace(/\.pdf$/i, '');
        titleInput.value = fileName;
      }
    }
  });
  
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
