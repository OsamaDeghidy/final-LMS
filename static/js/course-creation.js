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
  
  // Clone the module template
  const template = document.getElementById('module-template');
  const moduleElement = template.content.cloneNode(true).firstElementChild;
  moduleElement.id = moduleId;
  
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
  
  // Add PDF
  const addPdfBtn = moduleElement.querySelector('.add-pdf-btn');
  if (addPdfBtn) {
    addPdfBtn.addEventListener('click', () => addPdf(moduleElement, moduleId));
  }
  
  // Remove PDF buttons
  const removePdfBtns = moduleElement.querySelectorAll('.remove-pdf-btn');
  removePdfBtns.forEach(btn => {
    btn.addEventListener('click', () => btn.closest('.input-group').remove());
  });
  
  // Add note button
  const addNoteBtn = moduleElement.querySelector('.add-note-btn');
  if (addNoteBtn) {
    addNoteBtn.addEventListener('click', () => addNote(moduleElement, moduleId));
  }
  
  // Remove note buttons
  const removeNoteBtns = moduleElement.querySelectorAll('.remove-note-btn');
  removeNoteBtns.forEach(btn => {
    btn.addEventListener('click', () => removeNote(btn));
  });
  
  // Add video name button
  const addVideoNameBtn = moduleElement.querySelector('.add-title-btn');
  if (addVideoNameBtn) {
    addVideoNameBtn.addEventListener('click', () => addVideoName(moduleElement, moduleId));
  }
  
  // Remove video name buttons
  const removeVideoNameBtns = moduleElement.querySelectorAll('.remove-video-name-btn');
  removeVideoNameBtns.forEach(btn => {
    btn.addEventListener('click', () => removeVideoName(btn));
  });
  


  // Add material button
  const addMaterialBtn = moduleElement.querySelector('.add-material-btn');
  if (addMaterialBtn) {
    addMaterialBtn.addEventListener('click', () => addMaterial(moduleElement, moduleId));
  }
  
  // Add question button
  const addQuestionBtn = moduleElement.querySelector('.add-question-btn');
  if (addQuestionBtn) {
    addQuestionBtn.addEventListener('click', () => addQuestion(moduleElement, moduleId));
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
  const quizSection = moduleElement.querySelector('.quiz-section');
  if (quizSection) {
    quizSection.style.display = isChecked ? 'block' : 'none';
    
    // If showing the quiz section, make sure at least one question exists
    if (isChecked) {
      const questionsContainer = quizSection.querySelector('.questions-container');
      const visibleQuestions = Array.from(questionsContainer.querySelectorAll('.question-card'))
        .filter(q => q.style.display !== 'none');
      
      if (visibleQuestions.length === 0) {
        // Get the module ID from the add-question-btn
        const addQuestionBtn = quizSection.querySelector('.add-question-btn');
        if (addQuestionBtn) {
          const moduleId = addQuestionBtn.getAttribute('data-module-id');
          if (moduleId) {
            addQuestion(moduleElement, moduleId);
          }
        }
      }
    }
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
  // Increment question count for this module
  questionCounts[moduleId] = (questionCounts[moduleId] || 0) + 1;
  const questionIndex = questionCounts[moduleId];
  const questionId = `question_${moduleId}_${questionIndex}`;
  
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
  
  // Assemble all elements
  cardBody.appendChild(headerDiv);
  cardBody.appendChild(questionTextDiv);
  cardBody.appendChild(selectDiv);
  cardBody.appendChild(answersContainer);
  cardBody.appendChild(addAnswerBtn);
  questionCard.appendChild(cardBody);
  
  // Add to the questions container
  const questionsContainer = moduleElement.querySelector('.questions-container');
  questionsContainer.appendChild(questionCard);
  
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
  const answersContainer = questionElement.querySelector('.answers-container');
  const addAnswerBtn = questionElement.querySelector('.add-answer-btn');
  
  // Clear existing answers
  answersContainer.innerHTML = '';
  
  if (questionType === 'multiple_choice') {
    // Add default multiple choice answers
    // First answer
    const answer1Item = document.createElement('div');
    answer1Item.className = 'answer-item mb-2';
    
    const inputGroup1 = document.createElement('div');
    inputGroup1.className = 'input-group';
    
    const inputGroupText1 = document.createElement('div');
    inputGroupText1.className = 'input-group-text';
    
    const radioInput1 = document.createElement('input');
    radioInput1.className = 'form-check-input mt-0';
    radioInput1.type = 'radio';
    radioInput1.name = `correct_answer_${moduleId}_${questionIndex}`;
    radioInput1.value = '0';
    radioInput1.checked = true;
    
    const textInput1 = document.createElement('input');
    textInput1.type = 'text';
    textInput1.className = 'form-control';
    textInput1.name = `answer_text_${moduleId}_${questionIndex}_0`;
    textInput1.placeholder = 'الإجابة الأولى';
    textInput1.required = true;
    
    const removeBtn1 = document.createElement('button');
    removeBtn1.type = 'button';
    removeBtn1.className = 'btn btn-outline-danger remove-answer-btn';
    
    const removeIcon1 = document.createElement('i');
    removeIcon1.className = 'fas fa-times';
    
    // Assemble first answer
    removeBtn1.appendChild(removeIcon1);
    inputGroupText1.appendChild(radioInput1);
    inputGroup1.appendChild(inputGroupText1);
    inputGroup1.appendChild(textInput1);
    inputGroup1.appendChild(removeBtn1);
    answer1Item.appendChild(inputGroup1);
    
    // Second answer
    const answer2Item = document.createElement('div');
    answer2Item.className = 'answer-item mb-2';
    
    const inputGroup2 = document.createElement('div');
    inputGroup2.className = 'input-group';
    
    const inputGroupText2 = document.createElement('div');
    inputGroupText2.className = 'input-group-text';
    
    const radioInput2 = document.createElement('input');
    radioInput2.className = 'form-check-input mt-0';
    radioInput2.type = 'radio';
    radioInput2.name = `correct_answer_${moduleId}_${questionIndex}`;
    radioInput2.value = '1';
    
    const textInput2 = document.createElement('input');
    textInput2.type = 'text';
    textInput2.className = 'form-control';
    textInput2.name = `answer_text_${moduleId}_${questionIndex}_1`;
    textInput2.placeholder = 'الإجابة الثانية';
    textInput2.required = true;
    
    const removeBtn2 = document.createElement('button');
    removeBtn2.type = 'button';
    removeBtn2.className = 'btn btn-outline-danger remove-answer-btn';
    
    const removeIcon2 = document.createElement('i');
    removeIcon2.className = 'fas fa-times';
    
    // Assemble second answer
    removeBtn2.appendChild(removeIcon2);
    inputGroupText2.appendChild(radioInput2);
    inputGroup2.appendChild(inputGroupText2);
    inputGroup2.appendChild(textInput2);
    inputGroup2.appendChild(removeBtn2);
    answer2Item.appendChild(inputGroup2);
    
    // Add to container
    answersContainer.appendChild(answer1Item);
    answersContainer.appendChild(answer2Item);
    addAnswerBtn.style.display = 'block';
    
    // Add event listeners to the remove buttons
    const removeAnswerBtns = answersContainer.querySelectorAll('.remove-answer-btn');
    removeAnswerBtns.forEach(btn => {
      btn.addEventListener('click', function() {
        removeAnswer(this, answersContainer);
      });
    });
    
  } else if (questionType === 'true_false') {
    // Add true/false options using DOM manipulation
    // True answer
    const trueAnswerItem = document.createElement('div');
    trueAnswerItem.className = 'answer-item mb-2';
    
    const trueInputGroup = document.createElement('div');
    trueInputGroup.className = 'input-group';
    
    const trueInputGroupText = document.createElement('div');
    trueInputGroupText.className = 'input-group-text';
    
    const trueRadioInput = document.createElement('input');
    trueRadioInput.className = 'form-check-input mt-0';
    trueRadioInput.type = 'radio';
    trueRadioInput.name = `correct_answer_${moduleId}_${questionIndex}`;
    trueRadioInput.value = '0';
    trueRadioInput.checked = true;
    
    const trueTextInput = document.createElement('input');
    trueTextInput.type = 'text';
    trueTextInput.className = 'form-control';
    trueTextInput.name = `answer_text_${moduleId}_${questionIndex}_0`;
    trueTextInput.value = 'صح';
    trueTextInput.readOnly = true;
    
    // Assemble true answer
    trueInputGroupText.appendChild(trueRadioInput);
    trueInputGroup.appendChild(trueInputGroupText);
    trueInputGroup.appendChild(trueTextInput);
    trueAnswerItem.appendChild(trueInputGroup);
    
    // False answer
    const falseAnswerItem = document.createElement('div');
    falseAnswerItem.className = 'answer-item mb-2';
    
    const falseInputGroup = document.createElement('div');
    falseInputGroup.className = 'input-group';
    
    const falseInputGroupText = document.createElement('div');
    falseInputGroupText.className = 'input-group-text';
    
    const falseRadioInput = document.createElement('input');
    falseRadioInput.className = 'form-check-input mt-0';
    falseRadioInput.type = 'radio';
    falseRadioInput.name = `correct_answer_${moduleId}_${questionIndex}`;
    falseRadioInput.value = '1';
    
    const falseTextInput = document.createElement('input');
    falseTextInput.type = 'text';
    falseTextInput.className = 'form-control';
    falseTextInput.name = `answer_text_${moduleId}_${questionIndex}_1`;
    falseTextInput.value = 'خطأ';
    falseTextInput.readOnly = true;
    
    // Assemble false answer
    falseInputGroupText.appendChild(falseRadioInput);
    falseInputGroup.appendChild(falseInputGroupText);
    falseInputGroup.appendChild(falseTextInput);
    falseAnswerItem.appendChild(falseInputGroup);
    
    // Add to container
    answersContainer.appendChild(trueAnswerItem);
    answersContainer.appendChild(falseAnswerItem);
    addAnswerBtn.style.display = 'none';
    
  } else if (questionType === 'short_answer') {
    // Add short answer field using DOM manipulation
    const shortAnswerDiv = document.createElement('div');
    shortAnswerDiv.className = 'mb-3';
    
    const label = document.createElement('label');
    label.className = 'form-label';
    label.textContent = 'الإجابة الصحيحة';
    
    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'form-control';
    input.name = `answer_short_${moduleId}_${questionIndex}`;
    input.placeholder = 'أدخل الإجابة الصحيحة';
    input.required = true;
    
    shortAnswerDiv.appendChild(label);
    shortAnswerDiv.appendChild(input);
    answersContainer.appendChild(shortAnswerDiv);
    addAnswerBtn.style.display = 'none';
  }
}

function addAnswer(questionElement, moduleId, questionIndex) {
  const answersContainer = questionElement.querySelector('.answers-container');
  const answerCount = answersContainer.querySelectorAll('.answer-item').length;
  
  // Limit to 5 answers
  if (answerCount >= 5) {
    alert('لا يمكن إضافة أكثر من 5 إجابات');
    return;
  }
  
  // Create elements using DOM manipulation
  const answerItem = document.createElement('div');
  answerItem.className = 'answer-item mb-2';
  
  const inputGroup = document.createElement('div');
  inputGroup.className = 'input-group';
  
  const inputGroupText = document.createElement('div');
  inputGroupText.className = 'input-group-text';
  
  const radioInput = document.createElement('input');
  radioInput.className = 'form-check-input mt-0';
  radioInput.type = 'radio';
  radioInput.name = `correct_answer_${moduleId}_${questionIndex}`;
  radioInput.value = answerCount.toString();
  
  const textInput = document.createElement('input');
  textInput.type = 'text';
  textInput.className = 'form-control';
  textInput.name = `answer_text_${moduleId}_${questionIndex}_${answerCount}`;
  textInput.placeholder = 'أدخل الإجابة';
  textInput.required = true;
  
  const removeBtn = document.createElement('button');
  removeBtn.type = 'button';
  removeBtn.className = 'btn btn-outline-danger remove-answer-btn';
  
  const removeIcon = document.createElement('i');
  removeIcon.className = 'fas fa-times';
  
  // Assemble the elements
  removeBtn.appendChild(removeIcon);
  inputGroupText.appendChild(radioInput);
  inputGroup.appendChild(inputGroupText);
  inputGroup.appendChild(textInput);
  inputGroup.appendChild(removeBtn);
  answerItem.appendChild(inputGroup);
  answersContainer.appendChild(answerItem);
  
  // Add event listener to the new remove button
  removeBtn.addEventListener('click', function() {
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
  if (!validateForm()) {
    return;
  }

  const formData = new FormData(document.getElementById('course-form'));
  const submitBtn = document.getElementById('submit-course-btn');
  const originalText = submitBtn.innerHTML;
  submitBtn.disabled = true;
  
  // Create spinner icon using DOM manipulation
  const spinnerIcon = document.createElement('i');
  spinnerIcon.className = 'fas fa-spinner fa-spin me-2';
  
  // Clear button and add spinner + text
  submitBtn.innerHTML = '';
  submitBtn.appendChild(spinnerIcon);
  submitBtn.appendChild(document.createTextNode(' جاري الحفظ...'));

  // Variable to track validation
  let isValid = true;
  
  // Process modules
  const modules = document.querySelectorAll('.module-section');
  modules.forEach((module, index) => {
    const pdfContainer = module.querySelector('.pdf-container');
    const pdfInputs = pdfContainer.querySelectorAll('input[type="file"]');
    const pdfTitles = pdfContainer.querySelectorAll('input[type="text"]');

    // Update the count of PDFs for this module
    const pdfCount = pdfInputs.length;
    formData.set(`module_${index + 1}_pdf_count`, pdfCount.toString());

    // Check that each PDF has a title
    pdfInputs.forEach((input, i) => {
      if (input.files.length > 0 && !pdfTitles[i].value.trim()) {
        showAlert('danger', 'يجب إضافة عنوان لكل ملف PDF');
        isValid = false;
      }
    });
  });

  if (!isValid) {
    submitBtn.innerHTML = originalText;
    submitBtn.disabled = false;
    return;
  }

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
  const modules = document.querySelectorAll('.module-card');
  if (modules.length === 0) {
    showAlert('danger', 'يجب إضافة موديول واحد على الأقل');
    return false;
  }
  
  // Validate each module has either video or PDF content
  let hasContentError = false;
  modules.forEach(module => {
    const videos = module.querySelector('input[name^="module_videos_"]').files;
    const pdfs = module.querySelector('input[name^="module_pdfs_"]').files;
    
    if (videos.length === 0 && pdfs.length === 0) {
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
    const questions = moduleElement.querySelectorAll('.question-card');
    
    if (questions.length === 0) {
      showAlert('danger', 'يجب إضافة سؤال واحد على الأقل للاختبار');
      isValid = false;
    }
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
  
  const removeButton = document.createElement('button');
  removeButton.type = 'button';
  removeButton.className = 'btn btn-outline-danger remove-pdf-btn';
  removeButton.innerHTML = '<i class="fas fa-times"></i>';
  
  inputGroup.appendChild(fileInput);
  inputGroup.appendChild(removeButton);
  pdfContainer.appendChild(inputGroup);
  
  // Add event listener to the new remove button
  removeButton.addEventListener('click', () => inputGroup.remove());
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

// Export functions
module.exports = {
  addModule,
  removeModule,
  addNote,
  removeNote,
  addVideoName,
  removeVideoName,
  addQuestion,
  removeQuestion,
  addAnswer,
  removeAnswer,
  submitCourse,
  validateForm,
  showAlert,
  updateQuestionNumbering,
  initExistingModules,
  addPdf,
  addMaterial
};
