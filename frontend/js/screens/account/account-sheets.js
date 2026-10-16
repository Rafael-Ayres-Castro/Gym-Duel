// Dialogs of "Minha conta": change name, e-mail or password. All three are the same small
// form sheet, described by their fields, client checks and how server errors map to fields.
import { api, ApiError } from '../../core/api.js';
import { html, on } from '../../core/dom.js';
import { isDesktop } from '../../core/media.js';
import { EMAIL_PATTERN, fieldError, passwordToggle, setFieldError, togglePassword, withBusyButton } from '../../ui/form.js';
import { openSheet, sheetHead } from '../../ui/sheet.js';

const MIN_PASSWORD = 6;
const MAX_PASSWORD_BYTES = 72; // bcrypt limit, same check as the server

const fieldView = ({ name, label, type = 'text', value = '', autocomplete = 'off', hint = '', maxlength = 254 }) => {
  const isPassword = type === 'password';
  return html`
    <label class="field" data-field="${name}">
      <span class="label-caps">${label}</span>
      <span class="field__control">
        <input class="input input--tinted${isPassword ? ' input--with-action' : ''}" name="${name}" type="${type}"
          value="${value}" autocomplete="${autocomplete}" maxlength="${maxlength}"${type === 'email' ? html` inputmode="email"` : ''}>
        ${isPassword && passwordToggle()}
      </span>
      ${hint && html`<span class="field__hint">${hint}</span>`}
    </label>
    ${fieldError(`${name}-error`)}`;
};

const formView = ({ title, subtitle, fields, submitLabel }) => html`
  <form class="account-form" novalidate>
    ${sheetHead(title, subtitle)}
    <div class="sheet__body account-form__body">
      ${fields.map(fieldView)}
      ${fieldError('form-error')}
    </div>
    <footer class="sheet__foot">
      <button class="btn btn--secondary" type="button" data-action="close-sheet">Cancelar</button>
      <button class="btn btn--primary sheet__main" type="submit">${submitLabel}</button>
    </footer>
  </form>`;

/**
 * @param {object} o
 * @param {string} o.title
 * @param {string} o.subtitle
 * @param {object[]} o.fields                     see fieldView
 * @param {string} o.submitLabel
 * @param {string} o.busyLabel
 * @param {(values) => [string, string] | null} o.validate   [field, message] of the first problem
 * @param {(values) => Promise} o.submit
 * @param {Record<string, string>} [o.errorFields]           server error code → field that caused it
 * @param {() => void} o.onDone
 */
function openFormSheet({ title, subtitle, fields, submitLabel, busyLabel, validate, submit, errorFields = {}, onDone }) {
  const sheet = openSheet(formView({ title, subtitle, fields, submitLabel }), {
    label: title,
    size: 'sm',
    onAction: (action, target) => { if (action === 'toggle-password') togglePassword(target); },
  });
  const form = sheet.element.querySelector('form');
  // namedItem, not form[name]: form.name is the form's own attribute (see estado-do-projeto.md).
  const input = (name) => form.elements.namedItem(name);
  const values = () => Object.fromEntries(fields.map(({ name }) => [name, input(name).value]));
  const showError = (field, message) => {
    setFieldError(form, field, message);
    if (field !== 'form') input(field).select();
  };

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    [...fields.map(({ name }) => name), 'form'].forEach((name) => setFieldError(form, name, null));
    const data = values();
    const problem = validate(data);
    if (problem) return showError(...problem);
    try {
      await withBusyButton(form.querySelector('[type="submit"]'), busyLabel, () => submit(data));
      sheet.close();
      onDone();
    } catch (error) {
      if (!(error instanceof ApiError)) throw error;
      showError(errorFields[error.code] || 'form', error.message);
    }
  });
  // Typing in a field clears its own error, like the login form.
  on(form, 'input', 'input', (_, field) => setFieldError(form, field.name, null));
  // Only with a real keyboard; on phones it would cover the sheet.
  if (isDesktop()) input(fields[0].name).select();
}

const passwordProblem = (field, password) => {
  if (password.length < MIN_PASSWORD) return [field, `A senha precisa ter pelo menos ${MIN_PASSWORD} caracteres.`];
  if (new TextEncoder().encode(password).length > MAX_PASSWORD_BYTES) return [field, 'Essa senha é longa demais.'];
  return null;
};

export function openEditName(me, onDone) {
  openFormSheet({
    title: 'Alterar nome',
    subtitle: 'É assim que sua dupla vê você no placar.',
    fields: [{ name: 'full_name', label: 'Nome', value: me.name, autocomplete: 'name', maxlength: 60 }],
    submitLabel: 'Salvar nome',
    busyLabel: 'Salvando…',
    validate: ({ full_name: name }) => (name.trim() ? null : ['full_name', 'Digite seu nome.']),
    submit: ({ full_name: name }) => api.updateMe({ name: name.trim() }),
    onDone,
  });
}

export function openEditEmail(me, onDone) {
  openFormSheet({
    title: 'Alterar e-mail',
    subtitle: 'O novo e-mail passa a ser o seu login. Confirme com a senha atual.',
    fields: [
      { name: 'email', label: 'Novo e-mail', type: 'email', value: me.email, autocomplete: 'email' },
      { name: 'current_password', label: 'Senha atual', type: 'password', autocomplete: 'current-password', maxlength: 128 },
    ],
    submitLabel: 'Salvar e-mail',
    busyLabel: 'Salvando…',
    validate: ({ email, current_password: password }) => {
      if (!EMAIL_PATTERN.test(email.trim())) return ['email', 'Digite um e-mail válido.'];
      if (!password) return ['current_password', 'Digite sua senha atual.'];
      return null;
    },
    submit: ({ email, current_password: password }) => api.changeEmail(email.trim(), password),
    errorFields: { email_taken: 'email', wrong_password: 'current_password' },
    onDone,
  });
}

export function openEditPassword(onDone) {
  openFormSheet({
    title: 'Alterar senha',
    subtitle: 'Você continua conectado neste aparelho.',
    fields: [
      { name: 'current_password', label: 'Senha atual', type: 'password', autocomplete: 'current-password', maxlength: 128 },
      { name: 'new_password', label: 'Nova senha', type: 'password', autocomplete: 'new-password', maxlength: 128, hint: `Pelo menos ${MIN_PASSWORD} caracteres.` },
      { name: 'confirm_password', label: 'Repita a nova senha', type: 'password', autocomplete: 'new-password', maxlength: 128 },
    ],
    submitLabel: 'Salvar senha',
    busyLabel: 'Salvando…',
    validate: ({ current_password: current, new_password: next, confirm_password: confirm }) => {
      if (!current) return ['current_password', 'Digite sua senha atual.'];
      const problem = passwordProblem('new_password', next);
      if (problem) return problem;
      if (next !== confirm) return ['confirm_password', 'As senhas não são iguais.'];
      return null;
    },
    submit: ({ current_password: current, new_password: next }) => api.changePassword(current, next),
    errorFields: { wrong_password: 'current_password', same_password: 'new_password' },
    onDone,
  });
}
