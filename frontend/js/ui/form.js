// Form helpers shared by the login, sign up and account forms: inline errors and busy buttons.
import { html } from '../core/dom.js';
import { icon } from '../core/icons.js';

export const EMAIL_PATTERN = /^\S+@\S+\.\S+$/;

/** Inline error under a field: icon + text, hidden when empty. */
export const fieldError = (id) => html`
  <div class="form-error" id="${id}" role="alert" hidden>${icon('alert', 18, { stroke: 2.2 })}<span></span></div>`;

export function setFieldError(form, name, message) {
  const field = form.querySelector(`[data-field="${name}"]`);
  const error = form.querySelector(`#${name}-error`);
  field?.classList.toggle('has-error', Boolean(message));
  if (error) {
    error.hidden = !message;
    error.querySelector('span').textContent = message || '';
  }
}

/** Disable the submit button while a request runs, restoring its label afterwards. */
export async function withBusyButton(button, busyLabel, task) {
  const label = button.textContent;
  button.disabled = true;
  button.textContent = busyLabel;
  try {
    return await task();
  } finally {
    button.disabled = false;
    button.textContent = label;
  }
}

/** Eye button inside a password field (pair with `togglePassword`). */
export const passwordToggle = () => html`
  <button class="field__action" type="button" data-action="toggle-password" aria-label="Mostrar senha" aria-pressed="false">
    ${icon('eye', 20)}
  </button>`;

/** Show or hide the password of the field that holds `button`. */
export function togglePassword(button) {
  const input = button.closest('.field__control').querySelector('input');
  const visible = input.type === 'password';
  input.type = visible ? 'text' : 'password';
  button.setAttribute('aria-pressed', String(visible));
  button.setAttribute('aria-label', visible ? 'Esconder senha' : 'Mostrar senha');
}
