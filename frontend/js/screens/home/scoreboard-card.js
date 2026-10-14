// "Placar da semana" card: you vs. your duo by % of personal goal, plus the duel message.
// One markup for both layouts; home.css rearranges each panel with grid areas.
import { html } from '../../core/dom.js';
import { icon } from '../../core/icons.js';
import { daysLeft, streakLong, streakShort } from '../../domain/format.js';
import { goalCaption, playerState } from '../../domain/players.js';
import { avatar } from '../../ui/avatar.js';

function playerPanel(player) {
  const state = playerState(player);
  const lead = state === 'lead';
  return html`
    <article class="panel panel--${state} player--${player.color}" aria-label="${player.name}: ${player.pct}% da meta">
      <div class="panel__avatar">
        ${avatar({ name: player.name, color: player.color, ring: lead ? 'lead' : 'ring', crown: lead, badge: lead })}
      </div>
      <div class="panel__name">${player.name}</div>
      <div class="panel__pts"><span class="pill pill--pts">${player.points} pts</span></div>
      <div class="panel__pct">${player.pct}%</div>
      <div class="bar panel__bar"><div class="bar__fill" style="width:${player.pct}%"></div></div>
      <div class="panel__caption">${goalCaption(player)}</div>
      <div class="panel__streak">
        <span class="pill pill--fire">${icon('fire', 14)}<span class="only-mobile">${streakShort(player.streak)}</span><span class="only-desktop">${streakLong(player.streak)}</span></span>
      </div>
    </article>`;
}

const waitingPanel = () => html`
  <article class="panel panel--waiting">
    <div class="panel__avatar">${avatar({ name: '?', text: '?', ring: 'none' })}</div>
    <div class="panel__name">Sua dupla</div>
    <div class="panel__waiting">Aguardando sua dupla se cadastrar</div>
  </article>`;

export function scoreboardCard(board, me, opponent) {
  const days = daysLeft(board.today, board.week_end);
  return html`
    <section class="board" aria-label="Placar da semana">
      <div class="board__top">
        <span class="board__label">PLACAR<span class="only-desktop"> DA SEMANA</span> · % DA META</span>
        <span class="board__days"><span class="only-desktop">${days.weekday} · </span>${days.left}</span>
      </div>
      <div class="board__duel">
        ${playerPanel(me)}
        <div class="board__vs">VS</div>
        ${opponent ? playerPanel(opponent) : waitingPanel()}
      </div>
      <p class="board__msg">${icon('trophy', 18)}<span>${board.duel_message}</span></p>
    </section>`;
}
