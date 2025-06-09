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
  // Check if we already have a module with this count and increment if needed
  while (document.getElementById(`module_${moduleCount + 1}`)) {
    moduleCount++;
  }
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
  
  // Log for debugging
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