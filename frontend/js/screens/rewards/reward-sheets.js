// Dialogs of the rewards store: "Criar prêmio" and the redemption (confirm → success).
import { api, ApiError } from '../../core/api.js';
import { html } from '../../core/dom.js';
import { icon } from '../../core/icons.js';
import { openSheet, sheetHead } from '../../ui/sheet.js';

// ---- Criar prêmio ----

function createView({ duoName, costs, weekRef, cost }) {
  return html`
    ${sheetHead('Criar prêmio', `Algo que você topa fazer. ${duoName} resgata com os pontos que juntar.`)}
    <div class="sheet__body">
      <label class="field">
        <span class="label-caps">Prêmio</span>
        <input class="input" name="title" maxlength="80" autocomplete="off" placeholder="Ex.: Sobremesa feita por mim">
      </label>
      <div class="field">
        <span class="label-caps">Custo</span>
        <div class="cost-grid" role="radiogroup" aria-label="Custo em pontos">
          ${costs.map((value) => html`
            <button class="choice${value === cost ? ' is-on' : ''}" type="button" role="radio" aria-checked="${value === cost}" data-cost="${value}">
              <span class="choice__num">${value}</span><span class="choice__sub">pts</span>
            </button>`)}
        </div>
        <span class="field__hint">Referência: uma semana com a meta batida rende cerca de ${weekRef} pts.</span>
      </div>
      <div class="form-error" role="alert" hidden>${icon('alert', 18, { stroke: 2.2 })}<span></span></div>
    </div>
    <footer class="sheet__foot">
      <button class="btn btn--secondary" type="button" data-action="close-sheet">Cancelar</button>
      <button class="btn btn--primary sheet__main" type="button" data-action="save-reward" disabled>Adicionar à loja de ${duoName}</button>
    </footer>`;
}

export function openCreateReward({ duoName, costs, weekRef, onCreated }) {
  let cost = 100;
  const sheet = openSheet(createView({ duoName, costs, weekRef, cost }), {
    label: 'Criar prêmio',
    size: 'sm',
    onAction: async (action, target) => {
      if (action !== 'save-reward') return;
      const title = input.value.trim();
      if (!title) return;
      target.disabled = true;
      try {
        await api.createReward({ title, cost });
        sheet.close();
        onCreated(title);
      } catch (error) {
        if (!(error instanceof ApiError)) throw error;
        showError(error.message);
        target.disabled = false;
      }
    },
  });
  const { element } = sheet;
  const input = element.querySelector('[name="title"]');
  const save = element.querySelector('[data-action="save-reward"]');
  const showError = (message) => {
    const box = element.querySelector('.form-error');
    box.hidden = !message;
    box.querySelector('span').textContent = message || '';
  };
  input.addEventListener('input', () => { save.disabled = !input.value.trim(); });
  input.addEventListener('keydown', (event) => { if (event.key === 'Enter' && input.value.trim()) save.click(); });
  element.addEventListener('click', (event) => {
    const option = event.target.closest('[data-cost]');
    if (!option) return;
    cost = Number(option.dataset.cost);
    element.querySelectorAll('[data-cost]').forEach((button) => {
      button.classList.toggle('is-on', button === option);
      button.setAttribute('aria-checked', String(button === option));
    });
  });
  input.focus();
}

// ---- Resgate ----

const confirmView = ({ reward, balance, duoName }) => html`
  <div class="sheet__body sheet__body--top">
    <span class="label-caps">Resgatar prêmio</span>
    <h2 class="redeem__title">${reward.title}</h2>
    <div class="redeem__balance">
      <div><span>Saldo atual</span><strong>${balance} pts</strong></div>
      ${icon('arrowRight', 22, { stroke: 2.2 })}
      <div class="redeem__after"><span>Depois do resgate</span><strong>${balance - reward.cost} pts</strong></div>
    </div>
    <p class="redeem__note">Custa ${reward.cost} pts. ${duoName} recebe um aviso para cumprir e vocês combinam o melhor dia.</p>
    <div class="form-error" role="alert" hidden>${icon('alert', 18, { stroke: 2.2 })}<span></span></div>
  </div>
  <footer class="sheet__foot">
    <button class="btn btn--secondary" type="button" data-action="close-sheet">Cancelar</button>
    <button class="btn btn--primary sheet__main" type="button" data-action="confirm-redeem">Confirmar resgate</button>
  </footer>`;

const doneView = ({ reward, duoName }) => html`
  <div class="redeem-done">
    <div class="redeem-done__icon">${icon('trophy', 44, { stroke: 2.2 })}</div>
    <div class="redeem-done__title display">Resgatado!</div>
    <div class="redeem-done__name">${reward.title}</div>
    <p class="redeem-done__text">${duoName} recebeu um aviso. Quando o prêmio for cumprido, marque como recebido.</p>
    <div class="redeem-done__actions">
      <button class="btn btn--secondary" type="button" data-action="see-mine">Ver meus resgates</button>
      <button class="btn btn--primary" type="button" data-action="close-sheet">Voltar à loja</button>
    </div>
  </div>`;

export function openRedeem({ reward, balance, duoName, onRedeemed, onSeeMine }) {
  const sheet = openSheet(confirmView({ reward, balance, duoName }), {
    label: `Resgatar ${reward.title}`,
    size: 'sm',
    onAction: async (action, target) => {
      if (action === 'see-mine') {
        sheet.close();
        onSeeMine();
        return;
      }
      if (action !== 'confirm-redeem') return;
      target.disabled = true;
      target.textContent = 'Resgatando…';
      try {
        await api.redeem(reward.id);
        sheet.update(doneView({ reward, duoName }));
        onRedeemed();
      } catch (error) {
        if (!(error instanceof ApiError)) throw error;
        const box = sheet.element.querySelector('.form-error');
        box.hidden = false;
        box.querySelector('span').textContent = error.message;
        target.disabled = false;
        target.textContent = 'Confirmar resgate';
      }
    },
  });
}
