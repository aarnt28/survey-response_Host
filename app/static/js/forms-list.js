const container = document.getElementById("forms-container");
const template = document.getElementById("form-card-template");

async function loadForms() {
  try {
    const response = await fetch("/forms?include_archived=true");
    if (!response.ok) {
      throw new Error(`Unable to load forms (${response.status})`);
    }
    const forms = await response.json();
    renderForms(forms);
  } catch (error) {
    container.innerHTML = `<p class="error">${error.message}</p>`;
  }
}

function renderForms(forms) {
  if (!forms.length) {
    container.innerHTML = `<p>No forms have been created yet.</p>`;
    return;
  }

  const fragment = document.createDocumentFragment();
  forms.forEach((form) => {
    const card = template.content.firstElementChild.cloneNode(true);
    card.querySelector(".card__title").textContent = form.title;
    card.querySelector(".card__description").textContent = form.description || "No description provided.";
    card.querySelector(".card__slug").textContent = form.slug;
    card.querySelector(".card__version").textContent = `v${form.version}`;

    const openButton = card.querySelector('[data-role="open-form"]');
    openButton.href = `/ui/forms/${encodeURIComponent(form.slug)}`;

    const archiveBadge = card.querySelector('[data-role="archive-flag"]');
    if (form.is_archived) {
      archiveBadge.hidden = false;
      card.classList.add("card--archived");
    }

    fragment.appendChild(card);
  });

  container.replaceChildren(fragment);
}

loadForms();
