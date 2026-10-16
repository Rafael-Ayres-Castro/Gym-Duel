// Markup of "Desafios" (prototype v2): received, active with live progress, sent and finished.
import { html } from '../../core/dom.js';
import { icon } from '../../core/icons.js';
import {
  barWidth, endsLabel, periodLabel, resultLabel, stakeLabel, statusOf, valueLabel,
} from '../../domain/challenges.js';
import { avatar } from '../../ui/avatar.js';
import { pageHead } from '../../ui/page-head.js';

const period = (c) => periodLabel(c.period, c.starts_on, c.ends_on);
const stake = (c) => stakeLabel(c.stake_points, c.stake_text);

function incomingCard(c) {
  const author = c.players.find((p) => !p.is_me);
  return html`
    <article class="challenge-invite player--${author.color}">
      ${avatar({ name: author.name, color: author.color, size: 52 })}
      <div class="challenge-invite__text">
        <h3>${c.title}</h3>
        <p>${period(c)} · ${stake(c)}</p>
      </div>
      <div class="challenge-invite__actions">
        <button class="btn btn--secondary btn--sm" type="button" data-action="decline" data-id="${c.id}">Recusar</button>
        <button class="btn btn--primary btn--sm" type="button" data-action="accept" data-id="${c.id}">Aceitar desafio</button>
      </div>
    </article>`;
}

function progressRow(c, player, values) {
  const lead = c.leader_id === player.user_id;
  return html`
    <div class="challenge-player player--${player.color}">
      ${avatar({ name: player.name, color: player.color, size: 40, ring: lead ? 'lead-thin' : 'none', crown: lead })}
      <div class="challenge-player__main">
        <div class="challenge-player__top">
          <span>${player.is_me ? 'Você' : player.name}</span>
          <span class="${lead ? 'is-lead' : ''}">${valueLabel(c.kind, player.value)}</span>
        </div>
        <div class="bar"><div class="bar__fill" style="width:${barWidth(c.kind, player.value, values)}%"></div></div>
      </div>
    </div>`;
}

function activeCard(c) {
  const values = c.players.map((p) => p.value);
  const status = statusOf(c);
  const duo = c.players.find((p) => !p.is_me);
  return html`
    <article class="challenge-card">
      <header class="challenge-card__head">
        <div>
          <h3>${c.title}</h3>
          <p>Proposto por ${c.created_by_me ? 'você' : c.created_by_name} · ${period(c)}</p>
        </div>
        <span class="status-chip status-chip--accent">${endsLabel(c.period, c.ends_on)}</span>
      </header>
      ${c.players.map((player) => progressRow(c, player, values))}
      <footer class="challenge-card__foot">
        ${icon('trophy', 18)}
        <span class="challenge-card__stake">${stake(c)}</span>
        <span class="challenge-card__status${status.who ? ` is-${status.who} player--${duo.color}` : ''}">${status.text}</span>
      </footer>
    </article>`;
}

const outgoingCard = (c) => html`
  <article class="challenge-sent">
    <div class="challenge-sent__text">
      <h3>${c.title}</h3>
      <p>${period(c)} · ${stake(c)}</p>
    </div>
    <button class="btn btn--ghost btn--xs" type="button" data-action="cancel" data-id="${c.id}">Cancelar</button>
  </article>`;

function doneRow(c, myId) {
  const won = c.winner_id === myId;
  return html`
    <div class="challenge-done">
      ${c.winner_id
        ? avatar({ name: c.winner_name, color: c.winner_color, size: 36, crown: true })
        : avatar({ name: '=', text: '=', size: 36 })}
      <div class="challenge-done__text">
        <div class="challenge-done__title">${c.base_title}</div>
        <div class="challenge-done__period">${period(c)}</div>
      </div>
      <span class="challenge-done__result${c.winner_id ? (won ? ' is-me' : ` is-duo player--${c.winner_color}`) : ''}">${resultLabel(c, myId)}</span>
    </div>`;
}

export function challengesView({ board, me, duoName }) {
  return html`
    <div class="challenges">
      ${pageHead({
        kicker: 'Disputas extras, combinadas entre vocês dois',
        title: 'Desafios',
        action: html`<button class="btn btn--primary challenges__new" type="button" data-action="new-challenge">${icon('plus', 20, { stroke: 2.6 })}Novo desafio</button>`,
      })}

      ${board.incoming.length > 0 && html`
        <section class="challenges__section">
          <h2 class="label-caps challenges__invite-label player--${board.incoming[0].players.find((p) => !p.is_me).color}">${duoName} te desafiou</h2>
          ${board.incoming.map(incomingCard)}
        </section>`}

      <section class="challenges__section">
        <h2 class="label-caps">Em andamento</h2>
        ${board.active.length
          ? html`<div class="challenges__grid">${board.active.map(activeCard)}</div>`
          : html`<p class="empty-box">Nenhum desafio ativo. Crie um para dar um tempero extra à semana.</p>`}
      </section>

      ${board.outgoing.length > 0 && html`
        <section class="challenges__section">
          <h2 class="label-caps">Aguardando ${duoName} aceitar</h2>
          ${board.outgoing.map(outgoingCard)}
        </section>`}

      <section class="challenges__section">
        <h2 class="label-caps">Concluídos</h2>
        ${board.done.length
          ? html`<div class="challenges__done">${board.done.map((c) => doneRow(c, me.id))}</div>`
          : html`<p class="empty-box">Os desafios encerrados aparecem aqui, com quem venceu.</p>`}
      </section>
    </div>`;
}
