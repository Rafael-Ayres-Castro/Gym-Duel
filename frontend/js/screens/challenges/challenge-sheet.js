// "Novo desafio" dialog: model, workout type, period and stake, with a live preview.
// Updates only what changes (classes, preview) so the "combinado" input keeps focus.
import { api, ApiError } from '../../core/api.js';
import { html } from '../../core/dom.js';
import { icon } from '../../core/icons.js';
import {
  CHALLENGE_KINDS, CHALLENGE_STAKES, CHALLENGE_TYPES, challengeTitle, periodDates, periodLabel, stakeLabel,
} from '../../domain/challenges.js';
import { parseDate, shortDate } from '../../domain/format.js';
import { openSheet } from '../../ui/sheet.js';

const chips = (name, options) => html`
  <div class="checkin__chips" role="radiogroup">
    ${options.map((option) => html`
      <button class="chip" type="button" role="radio" data-field="${name}" data-value="${option.value}">${option.label}</button>`)}
  </div>`;

function view(duoName, todayIso) {
  const week = periodDates('week', todayIso);
  return html`
    <header class="sheet__head">
      <div>
        <h2>Novo desafio</h2>
        <p>${duoName} precisa aceitar para valer.</p>
      </div>
      <button class="icon-btn" type="button" data-action="close-sheet" aria-label="Fechar">${icon('close', 18, { stroke: 2.4 })}</button>
    </header>
    <div class="sheet__body">
      <section class="checkin__group">
        <span class="label-caps">Modelo</span>
        ${chips('kind', CHALLENGE_KINDS)}
      </section>
      <section class="checkin__group" data-hide-for-goal>
        <span class="label-caps">Tipo de treino</span>
        ${chips('workoutType', [{ value: '', label: 'Qualquer' }, ...CHALLENGE_TYPES.map((type) => ({ value: type, label: type }))])}
      </section>
      <section class="checkin__group" data-hide-for-goal>
        <span class="label-caps">Período</span>
        <div class="checkin__options checkin__options--2">
          <button class="choice" type="button" data-field="period" data-value="week">
            <span>Esta semana</span><span class="choice__sub">até ${shortDate(parseDate(week.ends))}</span>
          </button>
          <button class="choice" type="button" data-field="period" data-value="weekend">
            <span>Fim de semana</span><span class="choice__sub">sáb e dom</span>
          </button>
        </div>
      </section>
      <section class="checkin__group">
        <span class="label-caps">Vale</span>
        <div class="stake-grid">
          ${CHALLENGE_STAKES.map((points) => html`
            <button class="choice" type="button" data-field="stake" data-value="${points}"><span>+${points} pts</span></button>`)}
          <button class="choice" type="button" data-field="stake" data-value="text"><span>Combinado</span></button>
        </div>
        <input class="input stake-text" name="stake_text" maxlength="120" autocomplete="off" hidden
          placeholder="Ex.: quem perder faz o jantar de sexta" aria-label="Combinado">
        <span class="field__hint">Pontos de desafio são bônus para quem vence. Ninguém perde pontos.</span>
      </section>
      <div class="challenge-preview">
        ${icon('trophy', 22)}
        <div>
          <div class="challenge-preview__title" data-bind="title"></div>
          <div class="challenge-preview__sub" data-bind="sub"></div>
        </div>
      </div>
      <div class="form-error" role="alert" hidden>${icon('alert', 18, { stroke: 2.2 })}<span></span></div>
    </div>
    <footer class="sheet__foot sheet__foot--sticky">
      <button class="btn btn--secondary" type="button" data-action="close-sheet">Cancelar</button>
      <button class="btn btn--primary sheet__main" type="button" data-action="send">Enviar desafio para ${duoName}</button>
    </footer>`;
}

export function openNewChallenge({ duoName, todayIso, onSent }) {
  const draft = { kind: 'count', workoutType: '', period: 'week', stake: '20', text: '' };
  // "Primeiro a bater a meta" is always the whole week, for any workout type.
  const effective = () => (draft.kind === 'goal' ? { ...draft, workoutType: '', period: 'week' } : draft);

  const sheet = openSheet(view(duoName, todayIso), {
    label: 'Novo desafio',
    size: 'lg',
    onAction: async (action, target) => {
      if (action !== 'send' || target.disabled) return;
      const values = effective();
      target.disabled = true;
      try {
        await api.createChallenge({
          kind: values.kind,
          workout_type: values.workoutType || null,
          period: values.period,
          stake_points: values.stake === 'text' ? null : Number(values.stake),
          stake_text: values.stake === 'text' ? values.text.trim() : null,
        });
        sheet.close();
        onSent();
      } catch (error) {
        if (!(error instanceof ApiError)) throw error;
        const box = element.querySelector('.form-error');
        box.hidden = false;
        box.querySelector('span').textContent = error.message;
        target.disabled = false;
      }
    },
  });
  const { element } = sheet;
  const textInput = element.querySelector('[name="stake_text"]');

  function sync() {
    const values = effective();
    element.querySelectorAll('[data-field]').forEach((option) => {
      const selected = values[option.dataset.field] === option.dataset.value;
      option.classList.toggle('is-on', selected);
      option.setAttribute('aria-checked', String(selected));
    });
    element.querySelectorAll('[data-hide-for-goal]').forEach((section) => { section.hidden = draft.kind === 'goal'; });
    textInput.hidden = draft.stake !== 'text';
    const dates = periodDates(values.period, todayIso);
    element.querySelector('[data-bind="title"]').textContent = challengeTitle(values.kind, values.workoutType, values.period);
    element.querySelector('[data-bind="sub"]').textContent =
      `${periodLabel(values.period, dates.starts, dates.ends)} · ${stakeLabel(values.stake === 'text' ? null : Number(values.stake), values.text.trim())}`;
    element.querySelector('[data-action="send"]').disabled = draft.stake === 'text' && !draft.text.trim();
  }

  element.addEventListener('click', (event) => {
    const option = event.target.closest('[data-field]');
    if (!option) return;
    draft[option.dataset.field] = option.dataset.value;
    sync();
    if (option.dataset.value === 'text') textInput.focus();
  });
  textInput.addEventListener('input', () => { draft.text = textInput.value; sync(); });
  sync();
}
