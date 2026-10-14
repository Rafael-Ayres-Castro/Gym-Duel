// Login screen: e-mail + password, errors shown on the field that caused them.
import { api, ApiError } from '../../core/api.js';
import { html, on, renderInto } from '../../core/dom.js';
import { icon } from '../../core/icons.js';
import { isDesktop } from '../../core/media.js';
import { go } from '../../core/router.js';
import { session } from '../../core/session.js';
import { showToast } from '../../ui/toast.js';
import { authLayout, EMAIL_PATTERN, fieldError, mobileBrand, setFieldError, withBusyButton } from './auth-layout.js';

const view = (email) => authLayout(html`
  <form class="auth-form auth-form--login" novalidate>
    ${mobileBrand()}
    <div class="auth-form__head only-desktop">
      <h2>Entrar</h2>
      <p>Bom te ver de volta.</p>
    </div>
    <div class="auth-form__fields">
      <label class="field" data-field="email">
        <span class="field__label">E-mail</span>
        <span class="field__control">
          <span class="field__icon">${icon('mail', 20)}</span>
          <input class="input input--with-icon" name="email" type="email" inputmode="email" autocomplete="email"
            placeholder="seu@email.com" value="${email}">
        </span>
      </label>
      ${fieldError('email-error')}
      <label class="field" data-field="password">
        <span class="field__label">Senha</span>
        <span class="field__control">
          <span class="field__icon">${icon('lock', 20)}</span>
          <input class="input input--with-icon input--with-action input--tinted" name="password" type="password"
            autocomplete="current-password" placeholder="Sua senha">
          <button class="field__action" type="button" data-action="toggle-password" aria-label="Mostrar senha" aria-pressed="false">
            ${icon('eye', 20)}
          </button>
        </span>
      </label>
      ${fieldError('password-error')}
      <div class="auth-form__forgot">
        <button class="link-btn" type="button" data-action="forgot">Esqueci a senha</button>
      </div>
    </div>
    ${fieldError('form-error')}
    <button class="btn btn--primary btn--block auth-form__submit" type="submit">Entrar</button>
    <div class="auth-form__spacer only-mobile"></div>
    <div class="auth-form__divider only-desktop"></div>
    <p class="auth-form__switch">Novo por aqui? <button class="link-btn link-btn--strong" type="button" data-action="signup">Criar conta</button></p>
  </form>`);

/** Client-side checks, same order and texts as the prototype. Returns [field, message] or null. */
function validate(email, password) {
  if (!email) return ['email', 'Digite seu e-mail.'];
  if (!EMAIL_PATTERN.test(email)) return ['email', 'Digite um e-mail válido.'];
  if (!password) return ['password', 'Digite sua senha.'];
  return null;
}

const SERVER_ERROR_FIELD = { unknown_email: 'email', wrong_password: 'password' };

export function mount(root) {
  renderInto(root, view(session.lastEmail));
  const form = root.querySelector('form');

  const clearErrors = () => ['email', 'password', 'form'].forEach((name) => setFieldError(form, name, null));

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    clearErrors();
    const email = form.email.value.trim();
    const password = form.password.value;
    const problem = validate(email, password);
    if (problem) {
      setFieldError(form, ...problem);
      form[problem[0]].focus();
      return;
    }
    try {
      const auth = await withBusyButton(form.querySelector('[type=submit]'), 'Entrando…', () => api.login(email, password));
      session.start(auth);
      go('home');
    } catch (error) {
      if (!(error instanceof ApiError)) throw error;
      const field = SERVER_ERROR_FIELD[error.code] || 'form';
      setFieldError(form, field, error.message);
      if (field === 'password') form.password.select();
    }
  });

  // Typing in a field clears its own error, like the prototype.
  on(form, 'input', 'input', (_, input) => setFieldError(form, input.name, null));

  on(form, 'click', '[data-action]', (_, button) => {
    const action = button.dataset.action;
    if (action === 'signup') go('signup');
    if (action === 'forgot') showToast('Recuperação de senha chega na próxima fase.');
    if (action === 'toggle-password') {
      const visible = form.password.type === 'password';
      form.password.type = visible ? 'text' : 'password';
      button.setAttribute('aria-pressed', String(visible));
      button.setAttribute('aria-label', visible ? 'Esconder senha' : 'Mostrar senha');
    }
  });

  // Autofocus only with a real keyboard; on phones it would pop the keyboard over the screen.
  if (isDesktop()) (form.email.value ? form.password : form.email).focus();
}
