const body = document.body;
const slug = body.dataset.formSlug;
const formTitle = document.getElementById("form-title");
const formDescription = document.getElementById("form-description");
const formSlug = document.getElementById("form-slug");
const formVersion = document.getElementById("form-version");
const formStatus = document.getElementById("form-status");
const questionsContainer = document.getElementById("questions");
const messageEl = document.getElementById("form-message");
const versionList = document.getElementById("version-list");
const versionsCard = document.getElementById("versions-card");
const dynamicForm = document.getElementById("dynamic-form");

async function init() {
  await Promise.all([loadForm(), loadVersions()]);
  dynamicForm.addEventListener("submit", handleSubmit);
}

async function loadForm() {
  try {
    const response = await fetch(`/forms/${encodeURIComponent(slug)}`);
    if (!response.ok) {
      throw new Error(`Unable to load form (${response.status})`);
    }
    const form = await response.json();
    renderForm(form);
  } catch (error) {
    messageEl.textContent = error.message;
    dynamicForm.classList.add("is-disabled");
    dynamicForm.querySelector("button[type='submit']").disabled = true;
  }
}

async function loadVersions() {
  try {
    const response = await fetch(`/forms/${encodeURIComponent(slug)}/versions`);
    if (!response.ok) {
      throw new Error(`Unable to load version history (${response.status})`);
    }
    const versions = await response.json();
    renderVersions(versions);
  } catch (error) {
    versionsCard.hidden = true;
    console.error(error);
  }
}

function renderForm(form) {
  formTitle.textContent = form.title;
  formDescription.textContent = form.description || "";
  formSlug.textContent = form.slug;
  formVersion.textContent = `v${form.version}`;
  formStatus.textContent = form.is_archived ? "Archived" : "Active";

  if (form.is_archived) {
    messageEl.textContent = "This form is archived and cannot accept new responses.";
    dynamicForm.querySelector("button[type='submit']").disabled = true;
  }

  const fragment = document.createDocumentFragment();
  form.questions
    .slice()
    .sort((a, b) => a.position - b.position)
    .forEach((question) => {
      fragment.appendChild(createQuestionElement(question));
    });

  questionsContainer.replaceChildren(fragment);
}

function renderVersions(versions) {
  if (!versions.length) {
    versionsCard.hidden = true;
    return;
  }

  const items = versions
    .slice()
    .sort((a, b) => b.version - a.version)
    .map((version) => {
      const li = document.createElement("li");
      li.innerHTML = `<strong>Version v${version.version}</strong><span>${new Date(
        version.created_at
      ).toLocaleString()}</span>`;
      return li;
    });

  versionList.replaceChildren(...items);
}

function createQuestionElement(question) {
  const wrapper = document.createElement("div");
  wrapper.className = "question";
  wrapper.dataset.questionId = String(question.id);
  wrapper.dataset.questionType = question.type;
  wrapper.dataset.required = question.required ? "true" : "false";

  const label = document.createElement("label");
  label.htmlFor = `question-${question.id}`;
  label.textContent = `${question.prompt}${question.required ? " *" : ""}`;
  wrapper.appendChild(label);

  const metadata = question.metadata || {};
  const helpParts = [];
  if (metadata.min_value !== undefined) {
    helpParts.push(`min ${metadata.min_value}`);
  }
  if (metadata.max_value !== undefined) {
    helpParts.push(`max ${metadata.max_value}`);
  }
  if (metadata.pattern) {
    helpParts.push(`pattern ${metadata.pattern}`);
  }
  if (metadata.options && metadata.options.length) {
    helpParts.push(`${metadata.options.length} options`);
  }
  if (helpParts.length) {
    const helpText = document.createElement("p");
    helpText.className = "help-text";
    helpText.textContent = helpParts.join(" · ");
    wrapper.appendChild(helpText);
  }

  let field;
  switch (question.type) {
    case "short_text":
      field = document.createElement("input");
      field.type = "text";
      break;
    case "long_text":
      field = document.createElement("textarea");
      field.rows = 4;
      break;
    case "integer":
      field = document.createElement("input");
      field.type = "number";
      field.step = "1";
      break;
    case "decimal":
      field = document.createElement("input");
      field.type = "number";
      field.step = "any";
      break;
    case "single_choice":
    case "multiple_choice":
      return createChoiceQuestion(wrapper, question, metadata);
    default:
      field = document.createElement("input");
      field.type = "text";
  }

  field.id = `question-${question.id}`;
  field.name = `question-${question.id}`;
  field.dataset.questionId = String(question.id);
  field.dataset.questionType = question.type;
  if (question.required) {
    field.required = true;
  }
  if (metadata.placeholder) {
    field.placeholder = metadata.placeholder;
  }
  if (metadata.min_value !== undefined) {
    field.min = metadata.min_value;
  }
  if (metadata.max_value !== undefined) {
    field.max = metadata.max_value;
  }
  if (metadata.pattern) {
    field.pattern = metadata.pattern;
  }

  wrapper.appendChild(field);
  return wrapper;
}

function createChoiceQuestion(wrapper, question, metadata) {
  const list = document.createElement("ul");
  list.className = "choice-list";
  wrapper.appendChild(list);

  const options = metadata.options || [];
  options.forEach((option, index) => {
    const item = document.createElement("li");
    const input = document.createElement("input");
    const inputId = `question-${question.id}-option-${index}`;
    input.id = inputId;
    input.name = `question-${question.id}`;
    input.value = option.value;
    input.type = question.type === "single_choice" ? "radio" : "checkbox";
    if (question.required && question.type === "single_choice") {
      input.required = true;
    }

    const optionLabel = document.createElement("label");
    optionLabel.setAttribute("for", inputId);
    optionLabel.textContent = option.label;

    item.append(input, optionLabel);
    list.appendChild(item);
  });

  return wrapper;
}

async function handleSubmit(event) {
  event.preventDefault();
  const submitButton = dynamicForm.querySelector("button[type='submit']");
  if (submitButton.disabled) {
    return;
  }

  const answers = [];
  let hasError = false;
  questionsContainer.querySelectorAll(".question").forEach((questionEl) => {
    const id = Number(questionEl.dataset.questionId);
    const type = questionEl.dataset.questionType;
    const required = questionEl.dataset.required === "true";
    let value = "";

    if (type === "single_choice") {
      const checked = questionEl.querySelector("input[type='radio']:checked");
      value = checked ? checked.value : "";
    } else if (type === "multiple_choice") {
      const selected = Array.from(
        questionEl.querySelectorAll("input[type='checkbox']:checked")
      ).map((input) => input.value);
      value = selected.join(",");
    } else {
      const input = questionEl.querySelector("input, textarea");
      value = input ? input.value.trim() : "";
    }

    if (required && !value) {
      questionEl.classList.add("has-error");
      hasError = true;
    } else {
      questionEl.classList.remove("has-error");
    }

    if (value) {
      answers.push({ question_id: id, value });
    }
  });

  if (hasError) {
    messageEl.textContent = "Please complete all required questions.";
    return;
  }

  const formData = new FormData(dynamicForm);
  const payload = {
    respondent_identifier: formData.get("respondent_identifier") || null,
    notes: formData.get("notes") || null,
    answers,
  };

  submitButton.disabled = true;
  messageEl.textContent = "Submitting…";

  try {
    const response = await fetch(`/forms/${encodeURIComponent(slug)}/responses`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({}));
      throw new Error(errorBody.detail || `Submission failed (${response.status})`);
    }

    dynamicForm.reset();
    messageEl.textContent = "Response submitted successfully.";
  } catch (error) {
    messageEl.textContent = error.message;
  } finally {
    submitButton.disabled = false;
  }
}

init();
