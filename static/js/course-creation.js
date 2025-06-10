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

// Submit the course form
function submitCourse() {
  const form = document.getElementById('course-form');
  // If no action is set, use the current URL
  if (!form.getAttribute('action')) {
    form.setAttribute('action', window.location.pathname);
  }
  
  const formData = new FormData(form);
  const submitBtn = document.getElementById('submit-course-btn');
  const originalText = submitBtn.innerHTML;
  submitBtn.disabled = true;
  let isValid = true;

  // Clear previous error messages
  const alertsContainer = document.getElementById('alerts-container');
  alertsContainer.innerHTML = '';

  // Validate form before submission
  if (!validateCurrentStep()) {
    submitBtn.disabled = false;
    submitBtn.innerHTML = originalText;
    return;
  }

  // Show loading state
  submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>جاري الحفظ...';
  
  // Add CSRF token
  const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
  
  try {
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
    formData.append('module_count', modules.length);

    modules.forEach((module, moduleIndex) => {
      // Add module basic info
      const titleInput = module.querySelector('input[name^="module_name"]');
      const descriptionInput = module.querySelector('textarea[name^="module_description"]');
      
      formData.append(`module_${moduleIndex + 1}_title`, titleInput.value);
      if (descriptionInput) {
        formData.append(`module_${moduleIndex + 1}_description`, descriptionInput.value);
      }

      // Add video file and details
      const videoInput = module.querySelector('input[name^="module_video"]');
      const videoTitleInput = module.querySelector('input[name^="video_title"]');
      const videoDescInput = module.querySelector('textarea[name^="video_description"]');

      if (videoInput && videoInput.files.length > 0) {
        formData.append(`module_${moduleIndex + 1}_video`, videoInput.files[0]);
        formData.append(`module_${moduleIndex + 1}_video_title`, videoTitleInput.value);
        if (videoDescInput) {
          formData.append(`module_${moduleIndex + 1}_video_description`, videoDescInput.value);
        }
      }

      // Add PDF file and description
      const pdfInput = module.querySelector('input[name^="module_pdf"]');
      const pdfDescInput = module.querySelector('input[name^="pdf_description"]');

      if (pdfInput && pdfInput.files.length > 0) {
        formData.append(`module_${moduleIndex + 1}_pdf`, pdfInput.files[0]);
        if (pdfDescInput) {
          formData.append(`module_${moduleIndex + 1}_pdf_description`, pdfDescInput.value);
        }
      }

      // Add module notes
      const noteInput = module.querySelector('textarea[name^="module_note"]');
      if (noteInput && noteInput.value.trim()) {
        formData.append(`module_${moduleIndex + 1}_note`, noteInput.value);
      }
    });

    // Log form data for debugging
    console.log('Submitting form to:', form.action);
    for (let pair of formData.entries()) {
      console.log(pair[0] + ': ', pair[1]);
    }
    
    // Submit the form
    fetch(form.action, {
      method: 'POST',
      body: formData,
      headers: {
        'X-CSRFToken': csrftoken
      },
      credentials: 'same-origin'  // Ensure cookies are sent with the request
    })
    .then(async response => {
      const text = await response.text();
      console.log('Server response status:', response.status);
      console.log('Response content:', text.substring(0, 500) + (text.length > 500 ? '...' : ''));
      
      // First try to parse as JSON
      try {
        const data = JSON.parse(text);
        if (response.ok) {
          return data;
        }
        throw new Error(data.message || 'حدث خطأ في الخادم');
      } catch (e) {
        // If not JSON, it's probably HTML
        const parser = new DOMParser();
        const doc = parser.parseFromString(text, 'text/html');
        
        // Check for form validation errors
        const errorElements = doc.querySelectorAll('.errorlist, .is-invalid');
        if (errorElements.length > 0) {
          const errorMessages = [];
          errorElements.forEach(el => {
            if (el.textContent.trim()) {
              errorMessages.push(el.textContent.trim());
            }
          });
          
          const errorMessage = errorMessages.length > 0 
            ? errorMessages.join('\n')
            : 'الرجاء التحقق من صحة البيانات المدخلة';
          
          throw new Error(errorMessage);
        }
        
        // Check for success message
        const successMessage = doc.querySelector('.alert-success') || 
                              doc.querySelector('[class*="success"]');
        if (successMessage) {
          return { success: true, message: successMessage.textContent.trim() };
        }
        
        // Check for redirect
        const redirectMeta = doc.querySelector('meta[http-equiv="refresh"]');
        if (redirectMeta) {
          const content = redirectMeta.getAttribute('content');
          const urlMatch = content.match(/url=(.*)/i);
          if (urlMatch && urlMatch[1]) {
            return { redirect_url: urlMatch[1].trim() };
          }
        }
        
        // If we get here, it's an unexpected HTML response
        console.log('Unexpected HTML response:', text.substring(0, 500) + '...');
        throw new Error('تلقينا استجابة غير متوقعة من الخادم. الرجاء إعادة المحاولة.');
      }
    })
    .then(data => {
      if (data.redirect_url) {
        window.location.href = data.redirect_url;
      } else if (data.success || data.message) {
        showAlert('success', data.message || 'تم حفظ الدورة بنجاح');
        // Redirect to the courses list after a short delay
        setTimeout(() => {
          // Try to get the base URL from the form action or use the current path
          const formAction = form.getAttribute('action') || '';
          const baseUrl = formAction.split('/').slice(0, -1).join('/');
          window.location.href = baseUrl || '/dashboard/';
        }, 1500);
      }
    })
    .catch(error => {
      console.error('Submission error:', error);
      let errorMessage = 'حدث خطأ أثناء حفظ الدورة. يرجى التحقق من البيانات والمحاولة مرة أخرى.';
      
      // More specific error messages
      if (error.message.includes('Failed to fetch')) {
        errorMessage = 'تعذر الاتصال بالخادم. يرجى التحقق من اتصال الإنترنت والمحاولة مرة أخرى.';
      } else if (error.message.includes('NetworkError')) {
        errorMessage = 'خطأ في الشبكة. يرجى التحقق من اتصال الإنترنت والمحاولة مرة أخرى.';
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      showAlert('danger', errorMessage);
    })
    .finally(() => {
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalText;
    });

  } catch (error) {
    console.error('Error:', error);
    showAlert('danger', 'حدث خطأ أثناء تجهيز البيانات. يرجى المحاولة مرة أخرى.');
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
