// Wrap everything in an IIFE to prevent variable leakage
(function() {
// Global variables
let currentStep = 0;
let moduleCount = 0;
let questionCounter = 0;
const MAX_ANSWERS = 5;

// File type validation
const ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/jpg', 'image/gif'];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

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
  
  // Setup file input change handlers
  setupFileInput('image_course', 'image_preview', validateImageFile);
  setupFileInput('syllabus_pdf', 'syllabus_pdf_preview', validatePdfFile);
  setupFileInput('materials_pdf', 'materials_pdf_preview', validatePdfFile);
  
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



// Setup file input with preview and validation
function setupFileInput(inputId, previewId, validationFn) {
  const input = document.getElementById(inputId);
  const preview = document.getElementById(previewId);
  
  if (!input || !preview) return;
  
  input.addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    // Validate file
    const validation = validationFn(file);
    if (!validation.valid) {
      showAlert('danger', validation.message);
      input.value = '';
      preview.innerHTML = '';
      return;
    }
    
    // Show preview
    if (inputId === 'image_course') {
      const reader = new FileReader();
      reader.onload = function(e) {
        preview.innerHTML = `
          <div class="position-relative d-inline-block">
            <img src="${e.target.result}" class="img-thumbnail" style="max-height: 150px;">
            <button type="button" class="btn btn-sm btn-danger position-absolute top-0 end-0 m-1" 
                    onclick="document.getElementById('${inputId}').value=''; this.parentElement.remove()">
              <i class="fas fa-times"></i>
            </button>
          </div>
        `;
      };
      reader.readAsDataURL(file);
    } else {
      preview.innerHTML = `
        <div class="alert alert-info p-2 d-flex justify-content-between align-items-center">
          <span><i class="fas fa-file-pdf me-2"></i>${file.name}</span>
          <button type="button" class="btn btn-sm btn-outline-danger" 
                  onclick="document.getElementById('${inputId}').value=''; this.parentElement.remove()">
            <i class="fas fa-times"></i>
          </button>
        </div>
      `;
    }
  });
}

// Validate image file
function validateImageFile(file) {
  if (!ALLOWED_IMAGE_TYPES.includes(file.type)) {
    return {
      valid: false,
      message: 'نوع الملف غير مدعوم. يرجى تحميل صورة بصيغة JPG أو PNG أو GIF.'
    };
  }
  
  if (file.size > MAX_FILE_SIZE) {
    return {
      valid: false,
      message: 'حجم الملف كبير جداً. الحد الأقصى المسموح به هو 10 ميجابايت.'
    };
  }
  
  return { valid: true };
}

// Validate PDF file
function validatePdfFile(file) {
  if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
    return {
      valid: false,
      message: 'يجب أن يكون الملف من نوع PDF.'
    };
  }
  
  if (file.size > MAX_FILE_SIZE) {
    return {
      valid: false,
      message: 'حجم الملف كبير جداً. الحد الأقصى المسموح به هو 10 ميجابايت.'
    };
  }
  
  return { valid: true };
}

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

// Move navigation functions to global scope
window.goToNextStep = function() {
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
};

window.nextStep = function() {
  // Validate current step before proceeding
  if (validateCurrentStep()) {
    // If moving to the review step (step 3), update the summary
    if (currentStep === 1) {
      updateCourseSummary();
    }
    window.goToNextStep();
  }
};

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
      const moduleName = moduleElement.querySelector('input[name^="module_name"]')?.value || `Module ${index + 1}`;
      const moduleDescription = moduleElement.querySelector('textarea[name^="module_description"]')?.value || '';
      
      // Add module data to form
      formData.append(`module_${moduleId}_name`, moduleName);
      formData.append(`module_${moduleId}_description`, moduleDescription);
      
      // Process video file
      const videoInput = moduleElement.querySelector('input[type="file"][accept^="video/"]');
      if (videoInput && videoInput.files.length > 0) {
        // Use module-specific field name for the video
        formData.append(`module_${moduleId}_video`, videoInput.files[0]);
        
        // Add video title with module-specific field name
        const videoTitleInput = moduleElement.querySelector('input[name^="video_title"]');
        if (videoTitleInput && videoTitleInput.value) {
          formData.append(`module_${moduleId}_video_title`, videoTitleInput.value);
        } else {
          // Default title if none provided
          formData.append(`module_${moduleId}_video_title`, `Video for ${moduleName}`);
        }
      }
      
      // Process PDF file
      const pdfInput = moduleElement.querySelector('input[type="file"][accept=".pdf"]');
      if (pdfInput && pdfInput.files.length > 0) {
        formData.append(`module_${moduleId}_pdf`, pdfInput.files[0]);
        
        // Add PDF title if available
        const pdfTitleInput = moduleElement.querySelector('.pdf-title');
        if (pdfTitleInput && pdfTitleInput.value) {
          formData.append(`module_${moduleId}_pdf_title`, pdfTitleInput.value);
        }
      }
      
      // Process notes
      const noteInput = moduleElement.querySelector('textarea[name^="module_note"]');
      if (noteInput && noteInput.value) {
        formData.append(`module_${moduleId}_note`, noteInput.value);
      }
      
      // Process quiz if exists
      const quizToggle = moduleElement.querySelector('.quiz-toggle');
      if (quizToggle && quizToggle.checked) {
        const quizSection = moduleElement.querySelector('.quiz-section');
        if (!quizSection) return;
        
        const questions = quizSection.querySelectorAll('.question-card');
        if (questions.length === 0) return;
        
        // Add quiz flag for this module
        formData.append(`module_${moduleId}_has_quiz`, 'true');
        
        questions.forEach((question, qIndex) => {
          const questionId = question.dataset.questionId;
          const questionType = question.querySelector('.question-type').value;
          const questionText = question.querySelector('.question-text').value;
          const questionPoints = question.querySelector('.question-points').value;
          
          // Add question data with module-specific keys
          formData.append(`module_${moduleId}_question_${qIndex}_type`, questionType);
          formData.append(`module_${moduleId}_question_${qIndex}_text`, questionText);
          formData.append(`module_${moduleId}_question_${qIndex}_points`, questionPoints);
          
          // Handle answers based on question type
          if (questionType === 'short_answer') {
            const answerInput = question.querySelector('input[type="text"][name$="_answer"]');
            if (answerInput) {
              formData.append(`module_${moduleId}_question_${qIndex}_answer`, answerInput.value);
            }
          } else {
            // For MCQ and True/False
            const answerElements = question.querySelectorAll('.answer-card');
            let correctAnswerIndex = -1;
            
            answerElements.forEach((answerEl, aIndex) => {
              const textInput = answerEl.querySelector('.answer-text');
              const radioInput = answerEl.querySelector('input[type="radio"]');
              
              if (textInput) {
                // Add answer with index
                formData.append(`module_${moduleId}_question_${qIndex}_answer_${aIndex}`, textInput.value);
                
                // Check if this is the correct answer
                if (radioInput && radioInput.checked) {
                  correctAnswerIndex = aIndex;
                }
              }
            });
            
            // Add correct answer index
            if (correctAnswerIndex >= 0) {
              formData.append(`module_${moduleId}_question_${qIndex}_correct`, correctAnswerIndex);
            }
          }
        });
      }
    });
    
    // Log form data for debugging
    console.log('=== Form Data ===');
    for (let [key, value] of formData.entries()) {
      if (value instanceof File) {
        console.log(`${key}:`, {
          name: value.name,
          type: value.type,
          size: value.size
        });
      } else {
        console.log(`${key}:`, value);
      }
    }
    
    // Submit the form
    const response = await fetch(form.action, {
      method: 'POST',
      body: formData,
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': csrfToken
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

// Expose necessary functions to global scope
window.toggleQuiz = function(moduleElement, isChecked) {
  console.log('Toggling quiz (global):', { moduleId: moduleElement.id, isChecked });
  
  const quizSection = moduleElement.querySelector('.quiz-section');
  if (quizSection) {
    quizSection.style.display = isChecked ? 'block' : 'none';
    
    if (isChecked) {
      const questionsContainer = quizSection.querySelector('.questions-container');
      if (questionsContainer && questionsContainer.querySelectorAll('.question-card').length === 0) {
        window.addQuestion(moduleElement, moduleElement.id);
      }
    }
  }
};

// Close the IIFE
})();
