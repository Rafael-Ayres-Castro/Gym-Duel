// Markup of "Prêmios" (prototype v2): balances, tabs, the two store shelves and redemption lists.
import { html } from '../../core/dom.js';
import { icon } from '../../core/icons.js';
import { dayMonth, parseDate } from '../../domain/format.js';
import { avatar } from '../../ui/avatar.js';
import { pageHead } from '../../ui/page-head.js';

export const TABS = [
  { id: 'store', label: 'Loja' },
  { id: 'mine', label: 'Meus resgates' },
  { id: 'to_fulfill', label: 'Para cumprir' },
];

const balanceBox = (store) => html`
  <div class="balance-box">
    <div class="balance-box__mine">
      <span class="balance-box__label">SEU SALDO</span>
      <div class="balance-box__value"><span class="balance-box__num">${store.balance}</span><span>pts</span></div>
    </div>
    ${store.opponent_name && html`
      <div class="balance-box__divider"></div>
      <div class="balance-box__duo">
        <span>Saldo de ${store.opponent_name}</span>
        <strong class="player--${store.opponentColor}">${store.opponent_balance} pts</strong>
      </div>`}
  </div>`;

const tabs = (active, pendingCount) => html`
  <div class="segmented rewards-tabs" role="tablist">
    ${TABS.map((tab) => html`
      <button class="segmented__btn${tab.id === active ? ' is-on' : ''}" type="button" role="tab"
        aria-selected="${tab.id === active}" data-tab="${tab.id}">
        ${tab.label}${tab.id === 'to_fulfill' && pendingCount > 0 && html`<span class="count-badge count-badge--sm">${pendingCount}</span>`}
      </button>`)}
  </div>`;

function offeredToMeCard(reward, store) {
  const affordable = store.balance >= reward.cost;
  const progress = Math.min(100, Math.round((Math.max(0, store.balance) / reward.cost) * 100));
  return html`
    <article class="reward-card">
      <div class="reward-card__from">${avatar({ name: store.opponent_name, color: store.opponentColor, size: 22 })}Oferecido por ${store.opponent_name}</div>
      <h3 class="reward-card__title">${reward.title}</h3>
      <div class="reward-card__cost${affordable ? ' is-affordable' : ''}"><span class="reward-card__num">${reward.cost}</span><span>pts</span></div>
      ${!affordable && html`
        <div class="reward-card__short">
          <div class="bar bar--thin player--${store.myColor}"><div class="bar__fill" style="width:${progress}%"></div></div>
          <span>Faltam ${reward.cost - store.balance} pts</span>
        </div>`}
      <button class="btn btn--sm ${affordable ? 'btn--primary' : 'btn--secondary'}" type="button"
        data-action="redeem" data-id="${reward.id}" ${affordable ? '' : html`disabled`}>${affordable ? 'Resgatar' : 'Saldo insuficiente'}</button>
    </article>`;
}

function offeredByMeCard(reward, store, me) {
  const duoBalance = store.opponent_balance ?? 0;
  const duoHasIt = store.opponent_name && duoBalance >= reward.cost;
  const note = !store.opponent_name ? 'Sua dupla resgata' : duoHasIt
    ? `${store.opponent_name} já tem saldo`
    : `Faltam ${reward.cost - duoBalance} pts para ${store.opponent_name}`;
  return html`
    <article class="reward-card reward-card--mine">
      <div class="reward-card__from">${avatar({ name: me.first_name, color: me.color, size: 22 })}Oferecido por você</div>
      <h3 class="reward-card__title">${reward.title}</h3>
      <div class="reward-card__foot">
        <div class="reward-card__cost reward-card__cost--sm"><span class="reward-card__num">${reward.cost}</span><span>pts</span></div>
        <span class="reward-card__duo${duoHasIt ? ` is-ready player--${store.opponentColor}` : ''}">${note}</span>
      </div>
    </article>`;
}

function storeTab(store, me) {
  const duo = store.opponent_name;
  return html`
    <section class="rewards-shelf">
      <h2 class="label-caps">${duo ? `Oferecidos por ${duo}` : 'Oferecidos pela sua dupla'} · você resgata</h2>
      ${store.offered_to_me.length
        ? html`<div class="rewards-grid">${store.offered_to_me.map((reward) => offeredToMeCard(reward, store))}</div>`
        : html`<p class="empty-box">${duo
          ? `${duo} ainda não ofereceu prêmios. Quando oferecer, eles aparecem aqui.`
          : 'Quando sua dupla se cadastrar, os prêmios oferecidos por ela aparecem aqui.'}</p>`}
    </section>
    <section class="rewards-shelf">
      <h2 class="label-caps">Que você oferece · ${duo || 'sua dupla'} resgata</h2>
      <div class="rewards-grid">
        ${store.offered_by_me.map((reward) => offeredByMeCard(reward, store, me))}
        <button class="reward-new" type="button" data-action="new-reward">
          <span class="reward-new__icon">${icon('plus', 22, { stroke: 2.4 })}</span>
          <strong>Criar prêmio</strong>
          <span>Algo que você topa fazer por ${duo || 'sua dupla'}</span>
        </button>
      </div>
    </section>`;
}

const STATUS = {
  mine: {
    pending: (r) => ({ text: `Aguardando ${r.owner_name}`, tone: 'accent' }),
    fulfilled: (r) => ({ text: `${r.owner_name} cumpriu`, tone: 'accent' }),
    received: () => ({ text: 'Recebido', tone: 'muted' }),
  },
  to_fulfill: {
    pending: () => ({ text: 'Você precisa cumprir', tone: 'accent' }),
    fulfilled: (r) => ({ text: `Aguardando ${r.redeemer_name} confirmar`, tone: 'muted' }),
    received: () => ({ text: 'Cumprido', tone: 'muted' }),
  },
};

function redemptionRow(redemption, scope) {
  const status = STATUS[scope][redemption.status](redemption);
  const date = dayMonth(parseDate(redemption.redeemed_on));
  const isMine = scope === 'mine';
  return html`
    <div class="redemption-row">
      ${avatar({ name: isMine ? redemption.owner_name : redemption.redeemer_name, color: isMine ? redemption.owner_color : redemption.redeemer_color, size: 40 })}
      <div class="redemption-row__text">
        <div class="redemption-row__title">${isMine ? redemption.title : `${redemption.redeemer_name} resgatou: ${redemption.title}`}</div>
        <div class="redemption-row__sub">${isMine
          ? `Resgatado em ${date} · ${redemption.cost} pts · ${redemption.owner_name} cumpre`
          : `Em ${date} · ${redemption.cost} pts`}</div>
      </div>
      <span class="status-chip status-chip--${status.tone}">${status.text}</span>
      ${isMine && redemption.status === 'pending' && html`
        <button class="btn btn--secondary btn--xs" type="button" data-action="remind" data-id="${redemption.id}">Lembrar ${redemption.owner_name}</button>`}
      ${isMine && redemption.status !== 'received' && html`
        <button class="btn btn--primary btn--xs" type="button" data-action="receive" data-id="${redemption.id}">Recebi</button>`}
      ${!isMine && redemption.status === 'pending' && html`
        <button class="btn btn--primary btn--xs" type="button" data-action="fulfill" data-id="${redemption.id}">Marcar como cumprido</button>`}
    </div>`;
}

function redemptionsTab(list, scope, duoName) {
  if (!list.length) {
    const message = scope === 'mine'
      ? 'Você ainda não resgatou nada. Que tal escolher algo na loja?'
      : `Nenhum pedido de ${duoName || 'sua dupla'} por enquanto.`;
    return html`<p class="empty-box">${message}</p>`;
  }
  return html`<div class="redemption-list">${list.map((redemption) => redemptionRow(redemption, scope))}</div>`;
}

export function rewardsView({ store, me, tab, list, pendingCount }) {
  return html`
    <div class="rewards">
      <div class="rewards__top">
        <div class="rewards__intro">
          ${pageHead({ kicker: 'Mimos combinados entre vocês, pagos com pontos', title: 'Prêmios' })}
          <p class="rewards__lead">Treinos, desafios e selos de sequência viram saldo. Resgatar não muda o placar da semana.</p>
        </div>
        ${balanceBox(store)}
      </div>
      ${tabs(tab, pendingCount)}
      ${tab === 'store' ? storeTab(store, me) : redemptionsTab(list, tab, store.opponent_name)}
    </div>`;
}
