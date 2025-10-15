// Client-side handler for the Practice Overview form

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('practice-overview-form');
  const message = document.getElementById('form-message');

  if (!form) return;

  const submitButton = form.querySelector('[data-role="submit"]');

  form.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    message.textContent = '';
    message.classList.remove('error');
    message.classList.add('form-message');

    if (submitButton) {
      submitButton.disabled = true;
      submitButton.setAttribute('aria-busy', 'true');
    }

    const formData = new FormData(form);
    const payload = {};
    for (const [key, value] of formData.entries()) {
      if (key === 'workstations' && value !== '') {
        payload[key] = Number(value);
      } else if (key === 'onsite_server' || key === 'cloud_pms') {
        payload[key] = value === 'yes';
      } else {
        payload[key] = value;
      }
    }

    try {
      const res = await fetch('/ui/forms/practice-overview/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        message.classList.remove('form-message');
        message.classList.add('error');
        message.textContent = err.detail || 'Failed to submit — please try again.';
        return;
      }

      await res.json().catch(() => ({}));
      message.classList.remove('error');
      message.classList.add('form-message');
      message.textContent = 'Response submitted. Thank you!';
      form.reset();
    } catch (err) {
      message.classList.remove('form-message');
      message.classList.add('error');
      message.textContent = 'Network error — please try again.';
      console.error(err);
    } finally {
      if (submitButton) {
        submitButton.disabled = false;
        submitButton.removeAttribute('aria-busy');
      }
    }
  });
});
