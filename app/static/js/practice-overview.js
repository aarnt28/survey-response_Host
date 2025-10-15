// Client-side handler for the Practice Overview form

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('practice-overview-form');
  const message = document.getElementById('form-message');

  if (!form) return;

  form.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    message.textContent = '';

    const formData = new FormData(form);
    const payload = {};
    for (const [k, v] of formData.entries()) {
      // For radio groups, FormData will set the field name properly
      payload[k] = v;
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

      const body = await res.json().catch(() => ({}));
      message.classList.remove('error');
      message.classList.add('form-message');
      message.textContent = 'Response submitted. Thank you!';
      form.reset();
    } catch (err) {
      message.classList.remove('form-message');
      message.classList.add('error');
      message.textContent = 'Network error — please try again.';
      console.error(err);
    }
  });
});
