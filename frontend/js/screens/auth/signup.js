// Sign up: name, e-mail, password and weekly goal (1 to 7). Closed once the duo is complete.
import { api, ApiError } from '../../core/api.js';
import { html, on, renderInto } from '../../core/dom.js';
import { isDesktop } from '../../core/media.js';
import { go } from '../../core/router.js';
import { session } from '../../core/session.js';
import { firstName } from '../../domain/format.js';
import { GOAL_OPTIONS } from '../../domain/rules.js';
import { EMAIL_PATTERN, fieldError, setFieldError, withBusyButton } from '../../ui/form.js';
import { showToast } from '../../ui/toast.js';
import { authLayout, brandRow } from './auth-layout.js';

const DEFAULT_GOAL = 3;

const view = () => authLayout(html`
  <form class="auth-form auth-form--signup" novalidate>
    <div class="auth-form__brand only-mobile">${brandRow()}</div>
    <div class="auth-form__head">
      <h2>Criar conta</h2>
      <p>Leva menos de um minuto.</p>
    </div>
    <label class="field">
      <span class="field__label">Nome</span>
      <input class="input" name="name" autocomplete="given-name" maxlength="60" placeholder="Como quer ser chamado">
    </label>
    <label class="field">
      <span class="field__label">E-mail</span>
      <input class="input" name="email" type="email" inputmode="email" autocomplete="email" placeholder="seu@email.com">
    </label>
    <label class="field">
      <span class="field__label">Senha</span>
      <input class="input" name="password" type="password" autocomplete="new-password" placeholder="Mínimo de 6 caracteres">
    </label>
    <div class="field" role="radiogroup" aria-labelledby="goal-label">
      <span class="field__label" id="goal-label">Meta semanal</span>
      <div class="goal-grid">
        ${GOAL_OPTIONS.map((goal) => html`
          <button type="button" class="choice${goal === DEFAULT_GOAL ? ' is-on' : ''}" role="radio"
            aria-checked="${goal === DEFAULT_GOAL}" data-goal="${goal}" aria-label="${goal} treinos por semana">
            <span class="choice__num">${goal}</span>
          </button>`)}
      </div>
      <span class="field__hint">Treinos por semana. A meta define os seus 100% no placar. Dá para mudar depois.</span>
    </div>
    ${fieldError('form-error')}
    <button class="btn btn--primary btn--block" type="submit">Criar conta</button>
    <p class="auth-form__switch">Já tem conta? <button class="link-btn link-btn--strong" type="button" data-action="login">Entrar</button></p>
  </form>`);

function validate({ name, email, password }) {
  if (!name) return 'Digite seu nome.';
  if (!EMAIL_PATTERN.test(email)) return 'Digite um e-mail válido.';
  if (password.length < 6) return 'A senha precisa ter pelo menos 6 caracteres.';
  return null;
}

export function mount(root) {
  renderInto(root, view());
  const form = root.querySelector('form');
  let goal = DEFAULT_GOAL;

  on(form, 'click', '[data-goal]', (_, button) => {
    goal = Number(button.dataset.goal);
    form.querySelectorAll('[data-goal]').forEach((option) => {
      const selected = option === button;
      option.classList.toggle('is-on', selected);
      option.setAttribute('aria-checked', String(selected));
    });
  });
  on(form, 'click', '[data-action="login"]', () => go('login'));
  on(form, 'input', 'input', () => setFieldError(form, 'form', null));

  // form.name is the <form>'s own name attribute, so the "name" input is read through elements.
  const nameInput = form.elements.namedItem('name');

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const data = {
      name: nameInput.value.trim(),
      email: form.email.value.trim(),
      password: form.password.value,
      weekly_goal: goal,
    };
    const problem = validate(data);
    if (problem) return setFieldError(form, 'form', problem);
    try {
      const auth = await withBusyButton(form.querySelector('[type=submit]'), 'Criando conta…', () => api.register(data));
      session.start(auth);
      go('home');
      showToast(`Conta criada. Bem-vindo(a), ${firstName(auth.user.name)}!`);
    } catch (error) {
      if (!(error instanceof ApiError)) throw error;
      setFieldError(form, 'form', error.message);
    }
  });

  if (isDesktop()) nameInput.focus();
}
