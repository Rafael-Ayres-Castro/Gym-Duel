// Markup of the check-in form (mockup 3a on mobile, modal of the prototype on desktop).
// Selection state is applied afterwards by checkin-modal.js (`sync`), so this is static per open.
import { html } from '../core/dom.js';
import { icon } from '../core/icons.js';
import { addDays, parseDate, shortDate } from '../domain/format.js';
import { DURATION_PRESETS, intensityOptions, NOTE_MAX, WORKOUT_TYPES } from '../domain/rules.js';

const group = (label, content, extra = '') => html`
  <section class="checkin__group">
    <span class="label-caps">${label}${extra}</span>
    ${content}
  </section>`;

export const photoBonusLabel = (rules) => (rules.photo_bonus ? `+${rules.photo_bonus} pts` : 'sem bônus');

/** Empty state (add from camera or gallery) and the filled state (preview + remove). */
const photoPicker = (bonusLabel, opponentName) => html`
  <div class="photo-pick" data-photo-state="empty">
    <div class="photo-pick__empty">
      <label class="photo-pick__add">
        ${icon('camera', 26)}
        <span class="photo-pick__text">
          <strong>Adicionar foto</strong>
          <span>Tire na hora ou escolha da galeria. ${opponentName} vê no histórico.</span>
        </span>
        <input class="visually-hidden" type="file" accept="image/*" name="photo">
      </label>
      <label class="photo-pick__camera">
        ${icon('camera', 20)}<span>Câmera</span>
        <input class="visually-hidden" type="file" accept="image/*" capture="environment" name="photo-camera">
      </label>
    </div>
    <div class="photo-pick__filled">
      <img class="photo-pick__thumb" alt="Prévia da foto do treino">
      <div class="photo-pick__info">
        <strong>Foto adicionada</strong>
        <span>Treino verificado · ${bonusLabel}</span>
      </div>
      <button class="btn btn--secondary photo-pick__remove" type="button" data-action="remove-photo">Remover</button>
    </div>
    <div class="form-error photo-pick__error" role="alert" hidden>${icon('alert', 18, { stroke: 2.2 })}<span></span></div>
  </div>`;

export function checkinFormView(todayIso, rules, opponentName = 'Sua dupla') {
  const today = parseDate(todayIso);
  const days = [
    { value: 'today', label: 'Hoje', sub: shortDate(today) },
    { value: 'yesterday', label: 'Ontem', sub: shortDate(addDays(today, -1)) },
  ];
  return html`
    <div class="checkin__form">
      <header class="checkin__head">
        <div class="checkin__titles">
          <h2 id="checkin-title">Novo check-in</h2>
          <p>Pré-preenchido com seu último treino<span class="only-desktop">. Confira e salve.</span></p>
        </div>
        <button class="icon-btn checkin__close" type="button" data-action="close" aria-label="Fechar">${icon('close', 18, { stroke: 2.4 })}</button>
      </header>

      <div class="checkin__body">
        ${group('Tipo de treino', html`
          <div class="checkin__chips">
            ${WORKOUT_TYPES.map((type) => html`
              <button class="chip" type="button" data-set="type" data-value="${type}">
                ${icon('check', 16, { stroke: 3, cls: 'chip__check' })}${type}
              </button>`)}
          </div>`)}

        ${group('Duração', html`
          <div class="checkin__durations">
            ${DURATION_PRESETS.map((minutes) => html`
              <button class="choice" type="button" data-set="duration" data-value="${minutes}">
                <span class="choice__num">${minutes}</span><span class="choice__sub">min</span>
              </button>`)}
            <label class="checkin__custom">
              <span class="checkin__custom-label only-mobile">Outro tempo</span>
              <input name="custom" inputmode="numeric" autocomplete="off" maxlength="3" aria-label="Outro tempo, em minutos">
              <span class="checkin__custom-unit">min</span>
            </label>
          </div>
          <span class="checkin__dur-error" hidden>Digite uma duração entre 5 e 300 minutos.</span>`)}

        <div class="checkin__pair">
          ${group('Intensidade', html`
            <div class="checkin__options checkin__options--3">
              ${intensityOptions(rules).map((option) => html`
                <button class="choice" type="button" data-set="intensity" data-value="${option.value}">
                  <span>${option.value}</span><span class="choice__sub">${option.sub}</span>
                </button>`)}
            </div>`)}
          ${group('Data', html`
            <div class="checkin__options checkin__options--2">
              ${days.map((day) => html`
                <button class="choice checkin__day" type="button" data-set="day" data-value="${day.value}">
                  <span>${day.label}</span><span class="choice__sub">${day.sub}</span>
                </button>`)}
            </div>`)}
        </div>

        ${group('Observação', html`
          <textarea class="input textarea" name="note" rows="2" maxlength="${NOTE_MAX}"
            placeholder="Ex.: treino de perna, recorde no agachamento"></textarea>`, html` <span class="label-optional">(opcional)</span>`)}

        ${group('Foto como prova', photoPicker(photoBonusLabel(rules), opponentName), html` <span class="label-optional">(opcional · ${photoBonusLabel(rules)})</span>`)}
      </div>

      <footer class="checkin__foot">
        <div class="checkin__preview">
          <span class="checkin__gain">VOCÊ GANHA</span>
          <div class="checkin__points"><span class="checkin__pts" data-bind="points"></span><span>pontos</span></div>
          <span class="checkin__summary only-desktop" data-bind="summary"></span>
        </div>
        <div class="checkin__actions">
          <div class="form-error checkin__error" role="alert" hidden>${icon('alert', 18, { stroke: 2.2 })}<span></span></div>
          <button class="btn btn--primary" type="button" data-action="save">Salvar check-in</button>
          <span class="checkin__hint only-desktop">Enter para salvar · Esc para fechar</span>
        </div>
      </footer>
    </div>`;
}
