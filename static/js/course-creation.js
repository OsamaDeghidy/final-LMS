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

  // Initialize quiz section
  const quizElements = {
    toggle: moduleElement.querySelector('.quiz-toggle'),
    section: moduleElement.querySelector('.quiz-section'),
    addButton: moduleElement.querySelector('.add-question-btn')
  };

  if (quizElements.toggle && quizElements.section && quizElements.addButton) {
    quizElements.toggle.checked = false;
    quizElements.section.style.display = 'none';
    quizElements.addButton.setAttribute('data-module-id', moduleId);
  }

  // Add module to container
  const container = document.getElementById('modules-container');
  if (container) {
    container.appendChild(moduleElement);
    setupModuleEventListeners(moduleElement, moduleId);
  } else {
    console.error('Modules container not found');
    return;
  }
  
  // Update module number
  const moduleTitle = moduleElement.querySelector('.card-header h5');
  moduleTitle.innerHTML = `<i class="fas fa-layer-group text-primary me-2"></i>الموديول ${moduleCount}`;
  
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

function addNote(moduleElement, moduleId) {
  const notesContainer = moduleElement.querySelector('.notes-container');
  const noteCount = notesContainer.children.length;
  
  // Create elements using DOM manipulation
  const inputGroup = document.createElement('div');
  inputGroup.className = 'input-group mb-2';
  
  const textarea = document.createElement('textarea');
  textarea.className = 'form-control';
  textarea.name = `module_notes_${moduleId}_${noteCount}`;
  textarea.rows = 2;
  textarea.placeholder = 'أدخل ملاحظة';
  
  const removeBtn = document.createElement('button');
  removeBtn.type = 'button';
  removeBtn.className = 'btn btn-outline-danger remove-note-btn';
  
  const icon = document.createElement('i');
  icon.className = 'fas fa-times';
  
  // Assemble the elements
  removeBtn.appendChild(icon);
  inputGroup.appendChild(textarea);
  inputGroup.appendChild(removeBtn);
  notesContainer.appendChild(inputGroup);
  
  // Add event listener to the new remove button
  removeBtn.addEventListener('click', function() {
    removeNote(this);
  });
}

function removeNote(button) {
  button.closest('.input-group').remove();
}

function addVideoName(moduleElement, moduleId) {
  const namesContainer = moduleElement.querySelector('.video-names-container');
  const nameCount = namesContainer.children.length;
  
  // Create elements using DOM manipulation
  const inputGroup = document.createElement('div');
  inputGroup.className = 'input-group mb-2';
  
  const span = document.createElement('span');
  span.className = 'input-group-text bg-light';
  
  const icon = document.createElement('i');
  icon.className = 'fas fa-video text-primary';
  
  const input = document.createElement('input');
  input.type = 'text';
  input.className = 'form-control';
  input.name = `video_name_${moduleId}_${nameCount}`;
  input.placeholder = 'أدخل عنوان الفيديو';
  
  const removeBtn = document.createElement('button');
  removeBtn.type = 'button';
  removeBtn.className = 'btn btn-outline-danger remove-video-name-btn';
  
  const removeIcon = document.createElement('i');
  removeIcon.className = 'fas fa-times';
  
  // Assemble the elements
  span.appendChild(icon);
  removeBtn.appendChild(removeIcon);
  inputGroup.appendChild(span);
  inputGroup.appendChild(input);
  inputGroup.appendChild(removeBtn);
  namesContainer.appendChild(inputGroup);
  
  // Add event listener to the new remove button
  removeBtn.addEventListener('click', function() {
    removeVideoName(this);
  });
}

function removeVideoName(button) {
  button.closest('.input-group').remove();
}

// Question and Answer functions
function addQuestion(moduleElement, moduleId) {
  if (!moduleId) {
    console.error('Module ID is required to add a question');
    return;
  }

  questionCounts[moduleId] = (questionCounts[moduleId] || 0) + 1;
  const questionIndex = questionCounts[moduleId];
  const questionId = `question_${moduleId}_${questionIndex}`;

  console.log('Adding question:', { moduleId, questionIndex, questionId });
  
  // Create the question card using DOM manipulation
  const questionCard = document.createElement('div');
  questionCard.className = 'card mb-3 question-card';
  questionCard.id = questionId;
  
  const cardBody = document.createElement('div');
  cardBody.className = 'card-body';
  
  // Header with question number and remove button
  const headerDiv = document.createElement('div');
  headerDiv.className = 'd-flex justify-content-between align-items-center mb-3';
  
  const questionTitle = document.createElement('h6');
  questionTitle.className = 'mb-0';
  questionTitle.textContent = `سؤال #${questionIndex}`;
  
  const removeBtn = document.createElement('button');
  removeBtn.type = 'button';
  removeBtn.className = 'btn btn-sm btn-outline-danger remove-question-btn';
  removeBtn.setAttribute('data-question-id', questionId);
  
  const removeIcon = document.createElement('i');
  removeIcon.className = 'fas fa-times';
  removeBtn.appendChild(removeIcon);
  
  headerDiv.appendChild(questionTitle);
  headerDiv.appendChild(removeBtn);
  
  // Question text input
  const questionTextDiv = document.createElement('div');
  questionTextDiv.className = 'mb-3';
  
  const questionInput = document.createElement('input');
  questionInput.type = 'text';
  questionInput.className = 'form-control';
  questionInput.name = `question_text_${moduleId}_${questionIndex}`;
  questionInput.placeholder = 'نص السؤال';
  questionInput.required = true;
  
  questionTextDiv.appendChild(questionInput);
  
  // Question type select
  const selectDiv = document.createElement('div');
  selectDiv.className = 'mb-3';
  
  const selectElement = document.createElement('select');
  selectElement.className = 'form-select question-type-select';
  selectElement.name = `question_type_${moduleId}_${questionIndex}`;
  
  const optionMultiple = document.createElement('option');
  optionMultiple.value = 'multiple_choice';
  optionMultiple.textContent = 'اختيار من متعدد';
  
  const optionTrueFalse = document.createElement('option');
  optionTrueFalse.value = 'true_false';
  optionTrueFalse.textContent = 'صح أو خطأ';
  
  const optionShortAnswer = document.createElement('option');
  optionShortAnswer.value = 'short_answer';
  optionShortAnswer.textContent = 'إجابة قصيرة';
  
  selectElement.appendChild(optionMultiple);
  selectElement.appendChild(optionTrueFalse);
  selectElement.appendChild(optionShortAnswer);
  selectDiv.appendChild(selectElement);
  
  // Answers container
  const answersContainer = document.createElement('div');
  answersContainer.className = 'answers-container';
  
  // Add answer button
  const addAnswerBtn = document.createElement('button');
  addAnswerBtn.type = 'button';
  addAnswerBtn.className = 'btn btn-sm btn-outline-primary mt-2 add-answer-btn';
  
  const addIcon = document.createElement('i');
  addIcon.className = 'fas fa-plus me-1';
  
  addAnswerBtn.appendChild(addIcon);
  addAnswerBtn.appendChild(document.createTextNode('إضافة إجابة'));
  
  // Add click event to the add answer button
  addAnswerBtn.addEventListener('click', function() {
    console.log('Add answer button clicked for question:', questionId);
    addAnswer(questionCard, moduleId, questionIndex);
  });
  
  // Assemble all elements
  cardBody.appendChild(headerDiv);
  cardBody.appendChild(questionTextDiv);
  cardBody.appendChild(selectDiv);
  cardBody.appendChild(answersContainer);
  cardBody.appendChild(addAnswerBtn);
  
  // Add initial answer for multiple choice questions
  if (selectElement.value === 'multiple_choice') {
    addAnswer(questionCard, moduleId, questionIndex);
  }
  questionCard.appendChild(cardBody);
  
  // Add to the questions container
  const questionsContainer = moduleElement.querySelector('.questions-container');
  questionsContainer.appendChild(questionCard);
  
  // Create and set up add answer button
  const newAddAnswerBtn = document.createElement('button');
  newAddAnswerBtn.type = 'button';
  newAddAnswerBtn.className = 'btn btn-sm btn-outline-primary add-answer-btn mt-2';
  newAddAnswerBtn.innerHTML = '<i class="fas fa-plus me-1"></i>إضافة إجابة';
  newAddAnswerBtn.addEventListener('click', function() {
    addAnswer(questionCard, moduleId, questionIndex);
  });
  answersContainer.appendChild(newAddAnswerBtn);

  // Add event listeners to the question's buttons
  setupQuestionEventListeners(questionCard, moduleElement, moduleId, questionId);
  
  // Initialize with multiple choice answers by default
  updateAnswerFields(questionCard, 'multiple_choice', moduleId, questionIndex);
}

function setupQuestionEventListeners(questionElement, moduleElement, moduleId, questionId) {
  // Setup question type change
  const questionTypeSelect = questionElement.querySelector('.question-type-select');
  if (questionTypeSelect) {
    questionTypeSelect.addEventListener('change', function() {
      updateAnswerFields(questionElement, this.value, moduleId, questionId);
    });
  }
  
  // Setup remove question button
  const removeQuestionBtn = questionElement.querySelector('.remove-question-btn');
  if (removeQuestionBtn) {
    removeQuestionBtn.addEventListener('click', function() {
      const questionIdAttr = this.getAttribute('data-question-id');
      if (questionIdAttr) {
        // This is an existing question, mark it for deletion
        const deleteInput = document.getElementById(`delete_question_${questionIdAttr}`);
        if (deleteInput) {
          deleteInput.value = '1';
          questionElement.style.display = 'none';
        } else {
          removeQuestion(questionElement, moduleElement);
        }
      } else {
        removeQuestion(questionElement, moduleElement);
      }
    });
  }
}

function removeQuestion(questionElement, moduleElement) {
  // Get the parent container
  const questionsContainer = moduleElement.querySelector('.questions-container');
  
  // Check if this is an existing question
  if (questionElement.id && questionElement.id.startsWith('existing_question_')) {
    const questionId = questionElement.getAttribute('id').replace('existing_question_', '');
    const deleteInput = document.getElementById(`delete_question_${questionId}`);
    
    if (deleteInput) {
      deleteInput.value = '1';
      questionElement.style.display = 'none';
    } else {
      questionElement.remove();
    }
  } else {
    // For new questions, just remove the element
    questionElement.remove();
  }
  
  // Update question numbering
  updateQuestionNumbering(questionsContainer);
}

function updateAnswerFields(questionElement, questionType, moduleId, questionIndex) {
  console.log('Updating answer fields:', { moduleId, questionIndex, questionType });
  
  const answersContainer = questionElement.querySelector('.answers-container');
  const addAnswerBtn = questionElement.querySelector('.add-answer-btn');
  
  if (!answersContainer) {
    console.error('Answers container not found');
    return;
  }
  
  // Clear existing answers but keep the add answer button
  while (answersContainer.firstChild && !answersContainer.firstChild.classList?.contains('add-answer-btn')) {
    answersContainer.removeChild(answersContainer.firstChild);
  }
  
  // Show/hide add answer button based on question type
  if (questionType === 'multiple_choice') {
    addAnswerBtn.style.display = 'block';
    // Add two initial answers for multiple choice
    addAnswer(questionElement, moduleId, questionIndex);
    addAnswer(questionElement, moduleId, questionIndex);
    
    // Add event listeners to the remove buttons
    const removeAnswerBtns = answersContainer.querySelectorAll('.remove-answer-btn');
    removeAnswerBtns.forEach(btn => {
      btn.addEventListener('click', function() {
        removeAnswer(this, answersContainer);
      });
    });
    
  } else if (questionType === 'true_false') {
    addAnswerBtn.style.display = 'none';
    
    // Create true/false radio buttons
    const trueFalseDiv = document.createElement('div');
    trueFalseDiv.className = 'true-false-answers';
    
    // True option
    const trueDiv = document.createElement('div');
    trueDiv.className = 'form-check';
    const trueInput = document.createElement('input');
    trueInput.type = 'radio';
    trueInput.name = `correct_answer_${moduleId}_${questionIndex}`;
    trueInput.value = 'true';
    trueInput.id = `true_${moduleId}_${questionIndex}`;
    trueInput.className = 'form-check-input';
    const trueLabel = document.createElement('label');
    trueLabel.className = 'form-check-label';
    trueLabel.htmlFor = `true_${moduleId}_${questionIndex}`;
    trueLabel.textContent = 'صح';
    trueDiv.appendChild(trueInput);
    trueDiv.appendChild(trueLabel);
    
    // False option
    const falseDiv = document.createElement('div');
    falseDiv.className = 'form-check';
    const falseInput = document.createElement('input');
    falseInput.type = 'radio';
    falseInput.name = `correct_answer_${moduleId}_${questionIndex}`;
    falseInput.value = 'false';
    falseInput.id = `false_${moduleId}_${questionIndex}`;
    falseInput.className = 'form-check-input';
    const falseLabel = document.createElement('label');
    falseLabel.className = 'form-check-label';
    falseLabel.htmlFor = `false_${moduleId}_${questionIndex}`;
    falseLabel.textContent = 'خطأ';
    falseDiv.appendChild(falseInput);
    falseDiv.appendChild(falseLabel);
    
    trueFalseDiv.appendChild(trueDiv);
    trueFalseDiv.appendChild(falseDiv);
    
    // Insert before the add answer button
    if (addAnswerBtn) {
      answersContainer.insertBefore(trueFalseDiv, addAnswerBtn);
    } else {
      answersContainer.appendChild(trueFalseDiv);
    }
    
    // Set first option as default
    trueInput.checked = true;
  } else if (questionType === 'short_answer') {
    addAnswerBtn.style.display = 'none';
    
    // Create short answer input
    const shortAnswerDiv = document.createElement('div');
    shortAnswerDiv.className = 'short-answer-container';
    
    const inputGroup = document.createElement('div');
    inputGroup.className = 'input-group';
    
    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'form-control';
    input.name = `answer_short_${moduleId}_${questionIndex}`;
    input.placeholder = 'أدخل الإجابة الصحيحة';
    input.required = true;
    
    // Add a hidden input for the answer text to match the expected format
    const hiddenInput = document.createElement('input');
    hiddenInput.type = 'hidden';
    hiddenInput.name = `answer_text_${moduleId}_${questionIndex}_0`;
    hiddenInput.value = 'إجابة قصيرة';
    
    inputGroup.appendChild(input);
    shortAnswerDiv.appendChild(inputGroup);
    shortAnswerDiv.appendChild(hiddenInput);
    
    // Insert before the add answer button
    if (addAnswerBtn) {
      answersContainer.insertBefore(shortAnswerDiv, addAnswerBtn);
    } else {
      answersContainer.appendChild(shortAnswerDiv);
    }
  }
}

function addAnswer(questionElement, moduleId, questionIndex) {
  console.log('Adding answer:', { moduleId, questionIndex });
  
  if (!questionElement || !moduleId || !questionIndex) {
    console.error('Missing required parameters:', { questionElement, moduleId, questionIndex });
    return;
  }

  const answersContainer = questionElement.querySelector('.answers-container');
  if (!answersContainer) {
    console.error('Answers container not found');
    return;
  }

  const answerItems = answersContainer.querySelectorAll('.answer-item:not([style*="display: none"])');
  const answerCount = answerItems.length;
  console.log('Current answer count:', answerCount);

  // Limit to 5 answers
  if (answerCount >= 5) {
    showAlert('warning', 'لا يمكن إضافة أكثر من 5 إجابات');
    return;
  }

  try {
    // Create answer item
    const answerItem = document.createElement('div');
    answerItem.className = 'answer-item mb-2';

    // Create input group
    const inputGroup = document.createElement('div');
    inputGroup.className = 'input-group';

    // Create radio button container
    const inputGroupText = document.createElement('div');
    inputGroupText.className = 'input-group-text';

    // Create radio button for correct answer
    const radioInput = document.createElement('input');
    radioInput.type = 'radio';
    radioInput.className = 'form-check-input';
    radioInput.name = `correct_answer_${moduleId}_${questionIndex}`;
    radioInput.value = answerCount + 1; // Start from 1 instead of 0

    // Create text input for answer
    const textInput = document.createElement('input');
    textInput.type = 'text';
    textInput.className = 'form-control';
    textInput.name = `answer_text_${moduleId}_${questionIndex}_${answerCount + 1}`;
    textInput.placeholder = 'أدخل الإجابة';
    textInput.required = true;

    // Create remove button
    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'btn btn-outline-danger remove-answer-btn';
    removeBtn.innerHTML = '<i class="fas fa-times"></i>';

    // Assemble the elements
    inputGroupText.appendChild(radioInput);
    inputGroup.appendChild(inputGroupText);
    inputGroup.appendChild(textInput);
    inputGroup.appendChild(removeBtn);
    answerItem.appendChild(inputGroup);

    // Find the add answer button
    const addAnswerBtn = answersContainer.querySelector('.add-answer-btn');
    console.log('Found add answer button:', addAnswerBtn ? 'yes' : 'no');

    // Insert before the "Add Answer" button
    if (addAnswerBtn) {
      answersContainer.insertBefore(answerItem, addAnswerBtn);
    } else {
      answersContainer.appendChild(answerItem);
    }

    // Add event listener to the new remove button
    removeBtn.addEventListener('click', function() {
      removeAnswer(this, answersContainer);
    });

    // If this is the first answer, select it as correct by default
    if (answerCount === 0) {
      radioInput.checked = true;
    }

    // Focus the new text input
    textInput.focus();

    console.log('Answer added successfully');
  } catch (error) {
    console.error('Error adding answer:', error);
  }
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
  if (!validateForm()) {
    return;
  }

  const formData = new FormData(document.getElementById('course-form'));
  const submitBtn = document.getElementById('submit-course-btn');
  const originalText = submitBtn.innerHTML;
  submitBtn.disabled = true;
  let isValid = true; // Initialize isValid variable

  // Show loading state
  submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>جاري الحفظ...';

  // Process modules
  const modules = document.querySelectorAll('.module-card:not([style*="display: none"])');
  let moduleIndex = 0;

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
      const pdfTitles = pdfContainer.querySelectorAll('input[type="text"]');
      
      pdfInputs.forEach((input, idx) => {
        if (input.files.length > 0) {
          formData.append(`module_${moduleIndex}_pdf_${idx + 1}`, input.files[0]);
          if (pdfTitles[idx]) {
            formData.append(`module_${moduleIndex}_pdf_${idx + 1}_title`, pdfTitles[idx].value);
          }
        }
      });
      formData.append(`module_${moduleIndex}_pdf_count`, pdfInputs.length);
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
            formData.append(`module_${moduleIndex + 1}_question_${questionIndex + 1}_correct_answer`, correctAnswerIndex.toString());
          } 
          else if (questionType === 'true_false') {
            const trueRadio = question.querySelector('input[value="true"]');
            const falseRadio = question.querySelector('input[value="false"]');
            
            if (!trueRadio.checked && !falseRadio.checked) {
              console.error('No true/false option selected:', { moduleId, questionIndex });
              showAlert('danger', 'يجب اختيار إجابة صحيحة (صح أو خطأ)');
              submitBtn.disabled = false;
              submitBtn.innerHTML = originalText;
              isValid = false;
              return;
            }
            
            const correctAnswer = trueRadio.checked ? 'true' : 'false';
            formData.append(`module_${moduleIndex + 1}_question_${questionIndex + 1}_correct_answer`, correctAnswer);
          } 
          else if (questionType === 'short_answer') {
            const answerInput = question.querySelector('input[name^="answer_short_"]');
            const correctAnswer = answerInput.value.trim();
            
            if (!correctAnswer) {
              console.error('Empty short answer found:', { moduleId, questionIndex });
              showAlert('danger', 'يجب إدخال الإجابة الصحيحة للسؤال القصير');
              submitBtn.disabled = false;
              submitBtn.innerHTML = originalText;
              isValid = false;
              return;
            }
            
            formData.append(`module_${moduleIndex + 1}_question_${questionIndex + 1}_correct_answer`, correctAnswer);
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

const validateForm = function() {
  const form = document.getElementById('course-form');
  const requiredFields = form.querySelectorAll('[required]');
  
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
    showAlert('danger', 'يرجى ملء جميع الحقول المطلوبة');
    return false;
  }
  
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
const showAlert = function(type, message) {
  // Remove existing alerts
  const existingAlerts = document.querySelectorAll('.alert-custom');
  existingAlerts.forEach(alert => alert.remove());
  
  // Create new alert
  const alertDiv = document.createElement('div');
  alertDiv.className = `alert alert-${type} alert-dismissible fade show alert-custom`;
  alertDiv.style.position = 'fixed';
  alertDiv.style.top = '20px';
  alertDiv.style.right = '20px';
  alertDiv.style.zIndex = '9999';
  alertDiv.style.minWidth = '300px';
  alertDiv.innerHTML = `
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  `;
  
  // Add to body
  document.body.appendChild(alertDiv);
  
  // Auto remove after 5 seconds
  setTimeout(() => {
    if (alertDiv.parentNode) {
      alertDiv.remove();
    }
  }, 5000);
};

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
      fileNameSpan.className = 'selected-file-name';
      fileNameSpan.textContent = this.files[0].name;
      
      // Remove any existing file name display
      const existingFileName = inputGroup.querySelector('.selected-file-name');
      if (existingFileName) {
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
