// Global variables
let currentStep = 0;
let moduleCount = 0;
let questionCounts = {};

// Navigation functions
function goToNextStep() {
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
  }
}

function nextStep() {
  // Validate current step before proceeding
  if (validateCurrentStep()) {
    goToNextStep();
  }
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
    if (!field.value) {
      field.classList.add('is-invalid');
      isValid = false;
    } else {
      field.classList.remove('is-invalid');
    }
  });
  
  if (!isValid) {
    alert('يرجى ملء جميع الحقول المطلوبة');
  }
  
  return isValid;
}

// Module functions
function addModule() {
  moduleCount++;
  const moduleId = `module_${moduleCount}`;
  questionCounts[moduleId] = 0;
  
  const moduleHtml = `
    <div class="card mb-4 module-card" id="${moduleId}">
      <div class="card-header bg-light d-flex justify-content-between align-items-center">
        <h5 class="mb-0"><i class="fas fa-layer-group text-primary me-2"></i>الموديول ${moduleCount}</h5>
        <button type="button" class="btn btn-sm btn-outline-danger remove-module-btn">
          <i class="fas fa-trash"></i>
        </button>
      </div>
      <div class="card-body">
        <!-- Module Info -->
        <div class="mb-3">
          <label class="form-label fw-bold">اسم الموديول</label>
          <input type="text" class="form-control" name="module_name_${moduleId}" placeholder="أدخل اسم الموديول" required>
        </div>
        
        <!-- Videos -->
        <div class="mb-3">
          <label class="form-label fw-bold">تحميل الفيديوهات</label>
          <input type="file" class="form-control" name="module_videos_${moduleId}" accept="video/*" multiple>
          <small class="text-muted">الصيغ المدعومة: MP4, MOV, AVI</small>
        </div>
        
        <!-- Notes -->
        <div class="mb-3">
          <label class="form-label fw-bold">ملاحظات إضافية</label>
          <div class="d-flex justify-content-between align-items-center mb-2">
            <div></div>
            <button type="button" class="btn btn-sm btn-outline-primary add-note-btn">
              <i class="fas fa-plus me-1"></i>إضافة ملاحظة
            </button>
          </div>
          <div class="notes-container">
            <div class="input-group mb-2">
              <textarea class="form-control" name="module_notes_${moduleId}_0" rows="2" placeholder="أدخل ملاحظة"></textarea>
              <button type="button" class="btn btn-outline-danger remove-note-btn">
                <i class="fas fa-times"></i>
              </button>
            </div>
          </div>
        </div>
        
        <!-- Video Names -->
        <div class="mb-3">
          <label class="form-label fw-bold">عناوين الفيديوهات</label>
          <div class="d-flex justify-content-between align-items-center mb-2">
            <div></div>
            <button type="button" class="btn btn-sm btn-outline-primary add-video-name-btn">
              <i class="fas fa-plus me-1"></i>إضافة عنوان
            </button>
          </div>
          <div class="video-names-container">
            <div class="input-group mb-2">
              <span class="input-group-text bg-light"><i class="fas fa-video text-primary"></i></span>
              <input type="text" class="form-control" name="video_name_${moduleId}_0" placeholder="أدخل عنوان الفيديو">
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
              <input class="form-check-input quiz-toggle" type="checkbox" id="has_quiz_${moduleId}" name="has_quiz_${moduleId}">
              <label class="form-check-label fw-bold" for="has_quiz_${moduleId}">إضافة اختبار للموديول</label>
            </div>
          </div>
          <div class="quiz-section card-body" style="display: none;">
            <div class="mb-3">
              <label class="form-label fw-bold">عنوان الاختبار</label>
              <input type="text" class="form-control" name="quiz_title_${moduleId}" placeholder="أدخل عنوان الاختبار">
            </div>
            <div class="mb-3">
              <label class="form-label fw-bold">وصف الاختبار</label>
              <textarea class="form-control" name="quiz_description_${moduleId}" rows="2" placeholder="وصف مختصر للاختبار"></textarea>
            </div>
            <div class="row mb-3">
              <div class="col-md-6">
                <label class="form-label fw-bold">درجة النجاح (%)</label>
                <input type="number" class="form-control" name="quiz_pass_mark_${moduleId}" min="0" max="100" value="50">
              </div>
              <div class="col-md-6">
                <label class="form-label fw-bold">مدة الاختبار (دقائق)</label>
                <input type="number" class="form-control" name="quiz_time_limit_${moduleId}" min="1" value="10">
              </div>
            </div>
            
            <div class="questions-container">
              <!-- Questions will be added here -->
            </div>
            
            <button type="button" class="btn btn-primary w-100 mt-3 add-question-btn">
              <i class="fas fa-plus me-1"></i>إضافة سؤال جديد
            </button>
          </div>
        </div>
      </div>
    </div>
  `;
  
  document.getElementById('modules-container').insertAdjacentHTML('beforeend', moduleHtml);
  
  // Get the newly added module
  const moduleElement = document.getElementById(moduleId);
  
  // Add event listeners to the module's buttons
  setupModuleEventListeners(moduleElement, moduleId);
}

function setupModuleEventListeners(moduleElement, moduleId) {
  // Remove module button
  const removeModuleBtn = moduleElement.querySelector('.remove-module-btn');
  removeModuleBtn.addEventListener('click', function() {
    removeModule(moduleId);
  });
  
  // Quiz toggle
  const quizToggle = moduleElement.querySelector('.quiz-toggle');
  quizToggle.addEventListener('change', function() {
    toggleQuiz(moduleElement, this.checked);
  });
  
  // Add note button
  const addNoteBtn = moduleElement.querySelector('.add-note-btn');
  addNoteBtn.addEventListener('click', function() {
    addNote(moduleElement, moduleId);
  });
  
  // Remove note buttons
  const removeNoteBtns = moduleElement.querySelectorAll('.remove-note-btn');
  removeNoteBtns.forEach(btn => {
    btn.addEventListener('click', function() {
      removeNote(this);
    });
  });
  
  // Add video name button
  const addVideoNameBtn = moduleElement.querySelector('.add-video-name-btn');
  addVideoNameBtn.addEventListener('click', function() {
    addVideoName(moduleElement, moduleId);
  });
  
  // Remove video name buttons
  const removeVideoNameBtns = moduleElement.querySelectorAll('.remove-video-name-btn');
  removeVideoNameBtns.forEach(btn => {
    btn.addEventListener('click', function() {
      removeVideoName(this);
    });
  });
  
  // Add question button
  const addQuestionBtn = moduleElement.querySelector('.add-question-btn');
  addQuestionBtn.addEventListener('click', function() {
    addQuestion(moduleElement, moduleId);
  });
}

function removeModule(moduleId) {
  if (confirm('هل أنت متأكد من حذف هذا الموديول؟')) {
    document.getElementById(moduleId).remove();
    delete questionCounts[moduleId];
  }
}

function toggleQuiz(moduleElement, isChecked) {
  const quizSection = moduleElement.querySelector('.quiz-section');
  quizSection.style.display = isChecked ? 'block' : 'none';
  
  // Add first question if enabling quiz and no questions exist
  if (isChecked && moduleElement.querySelectorAll('.question-card').length === 0) {
    const moduleId = moduleElement.id;
    addQuestion(moduleElement, moduleId);
  }
}

function addNote(moduleElement, moduleId) {
  const notesContainer = moduleElement.querySelector('.notes-container');
  const noteCount = notesContainer.children.length;
  
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
  const newRemoveBtn = notesContainer.lastElementChild.querySelector('.remove-note-btn');
  newRemoveBtn.addEventListener('click', function() {
    removeNote(this);
  });
}

function removeNote(button) {
  button.closest('.input-group').remove();
}

function addVideoName(moduleElement, moduleId) {
  const namesContainer = moduleElement.querySelector('.video-names-container');
  const nameCount = namesContainer.children.length;
  
  const nameHtml = `
    <div class="input-group mb-2">
      <span class="input-group-text bg-light"><i class="fas fa-video text-primary"></i></span>
      <input type="text" class="form-control" name="video_name_${moduleId}_${nameCount}" placeholder="أدخل عنوان الفيديو">
      <button type="button" class="btn btn-outline-danger remove-video-name-btn">
        <i class="fas fa-times"></i>
      </button>
    </div>
  `;
  
  namesContainer.insertAdjacentHTML('beforeend', nameHtml);
  
  // Add event listener to the new remove button
  const newRemoveBtn = namesContainer.lastElementChild.querySelector('.remove-video-name-btn');
  newRemoveBtn.addEventListener('click', function() {
    removeVideoName(this);
  });
}

function removeVideoName(button) {
  button.closest('.input-group').remove();
}

// Question and Answer functions
function addQuestion(moduleElement, moduleId) {
  // Increment question count for this module
  questionCounts[moduleId] = (questionCounts[moduleId] || 0) + 1;
  const questionIndex = questionCounts[moduleId];
  const questionId = `question_${moduleId}_${questionIndex}`;
  
  const questionHtml = `
    <div class="card mb-3 question-card" id="${questionId}">
      <div class="card-body">
        <div class="d-flex justify-content-between align-items-center mb-3">
          <h6 class="mb-0">سؤال #${questionIndex}</h6>
          <button type="button" class="btn btn-sm btn-outline-danger remove-question-btn">
            <i class="fas fa-times"></i>
          </button>
        </div>
        
        <div class="mb-3">
          <input type="text" class="form-control" name="question_text_${moduleId}_${questionIndex}" placeholder="نص السؤال" required>
        </div>
        
        <div class="mb-3">
          <select class="form-select question-type-select" name="question_type_${moduleId}_${questionIndex}">
            <option value="multiple_choice">اختيار من متعدد</option>
            <option value="true_false">صح أو خطأ</option>
            <option value="short_answer">إجابة قصيرة</option>
          </select>
        </div>
        
        <div class="answers-container">
          <!-- Answers will be added here based on question type -->
        </div>
        
        <button type="button" class="btn btn-sm btn-outline-primary mt-2 add-answer-btn">
          <i class="fas fa-plus me-1"></i>إضافة إجابة
        </button>
      </div>
    </div>
  `;
  
  const questionsContainer = moduleElement.querySelector('.questions-container');
  questionsContainer.insertAdjacentHTML('beforeend', questionHtml);
  
  // Get the newly added question
  const questionElement = document.getElementById(questionId);
  
  // Add event listeners to the question's buttons
  setupQuestionEventListeners(questionElement, moduleElement, moduleId, questionId);
  
  // Initialize with multiple choice answers by default
  updateAnswerFields(questionElement, 'multiple_choice', moduleId, questionIndex);
}

function setupQuestionEventListeners(questionElement, moduleElement, moduleId, questionId) {
  // Remove question button
  const removeQuestionBtn = questionElement.querySelector('.remove-question-btn');
  removeQuestionBtn.addEventListener('click', function() {
    removeQuestion(questionElement, moduleElement);
  });
  
  // Question type select
  const questionTypeSelect = questionElement.querySelector('.question-type-select');
  questionTypeSelect.addEventListener('change', function() {
    updateAnswerFields(questionElement, this.value, moduleId, questionId.split('_')[2]);
  });
  
  // Add answer button
  const addAnswerBtn = questionElement.querySelector('.add-answer-btn');
  addAnswerBtn.addEventListener('click', function() {
    addAnswer(questionElement, moduleId, questionId.split('_')[2]);
  });
}

function removeQuestion(questionElement, moduleElement) {
  const questionsContainer = moduleElement.querySelector('.questions-container');
  if (questionsContainer.querySelectorAll('.question-card').length > 1) {
    questionElement.remove();
  } else {
    alert('يجب أن يحتوي الاختبار على سؤال واحد على الأقل');
  }
}

function updateAnswerFields(questionElement, questionType, moduleId, questionIndex) {
  const answersContainer = questionElement.querySelector('.answers-container');
  const addAnswerBtn = questionElement.querySelector('.add-answer-btn');
  
  // Clear existing answers
  answersContainer.innerHTML = '';
  
  if (questionType === 'multiple_choice') {
    // Add default multiple choice answers
    const answer1Html = `
      <div class="answer-item mb-2">
        <div class="input-group">
          <div class="input-group-text">
            <input class="form-check-input mt-0" type="radio" name="correct_answer_${moduleId}_${questionIndex}" value="0" checked>
          </div>
          <input type="text" class="form-control" name="answer_text_${moduleId}_${questionIndex}_0" placeholder="الإجابة الأولى" required>
          <button type="button" class="btn btn-outline-danger remove-answer-btn">
            <i class="fas fa-times"></i>
          </button>
        </div>
      </div>
    `;
    
    const answer2Html = `
      <div class="answer-item mb-2">
        <div class="input-group">
          <div class="input-group-text">
            <input class="form-check-input mt-0" type="radio" name="correct_answer_${moduleId}_${questionIndex}" value="1">
          </div>
          <input type="text" class="form-control" name="answer_text_${moduleId}_${questionIndex}_1" placeholder="الإجابة الثانية" required>
          <button type="button" class="btn btn-outline-danger remove-answer-btn">
            <i class="fas fa-times"></i>
          </button>
        </div>
      </div>
    `;
    
    answersContainer.insertAdjacentHTML('beforeend', answer1Html);
    answersContainer.insertAdjacentHTML('beforeend', answer2Html);
    addAnswerBtn.style.display = 'block';
    
    // Add event listeners to the remove buttons
    const removeAnswerBtns = answersContainer.querySelectorAll('.remove-answer-btn');
    removeAnswerBtns.forEach(btn => {
      btn.addEventListener('click', function() {
        removeAnswer(this, answersContainer);
      });
    });
    
  } else if (questionType === 'true_false') {
    // Add true/false options
    const trueAnswerHtml = `
      <div class="answer-item mb-2">
        <div class="input-group">
          <div class="input-group-text">
            <input class="form-check-input mt-0" type="radio" name="correct_answer_${moduleId}_${questionIndex}" value="0" checked>
          </div>
          <input type="text" class="form-control" name="answer_text_${moduleId}_${questionIndex}_0" value="صح" readonly>
        </div>
      </div>
    `;
    
    const falseAnswerHtml = `
      <div class="answer-item mb-2">
        <div class="input-group">
          <div class="input-group-text">
            <input class="form-check-input mt-0" type="radio" name="correct_answer_${moduleId}_${questionIndex}" value="1">
          </div>
          <input type="text" class="form-control" name="answer_text_${moduleId}_${questionIndex}_1" value="خطأ" readonly>
        </div>
      </div>
    `;
    
    answersContainer.insertAdjacentHTML('beforeend', trueAnswerHtml);
    answersContainer.insertAdjacentHTML('beforeend', falseAnswerHtml);
    addAnswerBtn.style.display = 'none';
    
  } else if (questionType === 'short_answer') {
    // Add short answer field
    const shortAnswerHtml = `
      <div class="mb-3">
        <label class="form-label">الإجابة الصحيحة</label>
        <input type="text" class="form-control" name="answer_short_${moduleId}_${questionIndex}" placeholder="أدخل الإجابة الصحيحة" required>
      </div>
    `;
    
    answersContainer.insertAdjacentHTML('beforeend', shortAnswerHtml);
    addAnswerBtn.style.display = 'none';
  }
}

function addAnswer(questionElement, moduleId, questionIndex) {
  const answersContainer = questionElement.querySelector('.answers-container');
  const answerCount = answersContainer.querySelectorAll('.answer-item').length;
  
  // Limit to 5 answers
  if (answerCount >= 5) {
    alert('الحد الأقصى للإجابات هو 5');
    return;
  }
  
  const answerHtml = `
    <div class="answer-item mb-2">
      <div class="input-group">
        <div class="input-group-text">
          <input class="form-check-input mt-0" type="radio" name="correct_answer_${moduleId}_${questionIndex}" value="${answerCount}">
        </div>
        <input type="text" class="form-control" name="answer_text_${moduleId}_${questionIndex}_${answerCount}" placeholder="الإجابة ${answerCount + 1}" required>
        <button type="button" class="btn btn-outline-danger remove-answer-btn">
          <i class="fas fa-times"></i>
        </button>
      </div>
    </div>
  `;
  
  answersContainer.insertAdjacentHTML('beforeend', answerHtml);
  
  // Add event listener to the new remove button
  const newRemoveBtn = answersContainer.lastElementChild.querySelector('.remove-answer-btn');
  newRemoveBtn.addEventListener('click', function() {
    removeAnswer(this, answersContainer);
  });
}

function removeAnswer(button, answersContainer) {
  if (answersContainer.querySelectorAll('.answer-item').length > 2) {
    const answerItem = button.closest('.answer-item');
    answerItem.remove();
    
    // Renumber remaining answers
    const answerItems = answersContainer.querySelectorAll('.answer-item');
    answerItems.forEach((item, index) => {
      const radio = item.querySelector('input[type="radio"]');
      radio.value = index;
      
      const textInput = item.querySelector('input[type="text"]:not([readonly])');
      if (textInput) {
        const name = textInput.name;
        const newName = name.replace(/_(\d+)$/, `_${index}`);
        textInput.name = newName;
      }
    });
  } else {
    alert('يجب أن يحتوي السؤال على إجابتين على الأقل');
  }
}

// Submit the course form
function submitCourse() {
  if (validateForm()) {
    document.getElementById('course-form').submit();
  }
}

function validateForm() {
  // Validate required fields
  const requiredFields = document.querySelectorAll('[required]');
  let isValid = true;
  
  requiredFields.forEach(field => {
    if (!field.value) {
      field.classList.add('is-invalid');
      isValid = false;
    } else {
      field.classList.remove('is-invalid');
    }
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

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
  // Add event listener to the "Add Module" button
  const addModuleBtn = document.getElementById('add-module-btn');
  if (addModuleBtn) {
    addModuleBtn.addEventListener('click', addModule);
  }
  
  // Add event listener to the "Submit" button
  const submitBtn = document.getElementById('submit-course-btn');
  if (submitBtn) {
    submitBtn.addEventListener('click', function(e) {
      e.preventDefault();
      submitCourse();
    });
  }
});
