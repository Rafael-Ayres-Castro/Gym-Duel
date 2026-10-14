// Desktop-only "Dias de treino": a Mon–Sun grid per player, today highlighted.
import { html } from '../../core/dom.js';
import { DAY_INITIALS, daysMessage, parseDate, weekdayIndex } from '../../domain/format.js';
import { avatar } from '../../ui/avatar.js';

function playerRow(player, todayIndex) {
  return html`
    <span class="days-grid__who">${avatar({ name: player.name, color: player.color, size: 26 })}<span>${player.name}</span></span>
    ${player.days.map((trained, index) => html`
      <span class="days-grid__cell player--${player.color}${trained ? ' is-trained' : ''}${!trained && index === todayIndex ? ' is-today' : ''}"
        title="${trained ? 'Treinou' : 'Sem treino'}"></span>`)}`;
}

export function trainingDays(board, me) {
  const todayIndex = weekdayIndex(parseDate(board.today));
  return html`
    <section class="days-card only-desktop" aria-label="Dias de treino da semana">
      <h2>Dias de treino</h2>
      <div class="days-grid">
        <span></span>
        ${DAY_INITIALS.map((letter, index) => html`<span class="days-grid__head${index === todayIndex ? ' is-today' : ''}">${letter}</span>`)}
        ${board.players.map((player) => playerRow(player, todayIndex))}
      </div>
      <p class="days-card__msg">${daysMessage(board.today, me)}</p>
    </section>`;
}
