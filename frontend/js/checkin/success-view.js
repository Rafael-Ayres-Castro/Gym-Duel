// Celebration after saving (mockup 3b / prototype success): points, headline, mini scoreboard, streak pill.
import { html } from '../core/dom.js';
import { icon } from '../core/icons.js';
import { dayLabel } from '../domain/format.js';
import { splitPlayers } from '../domain/players.js';
import { avatar } from '../ui/avatar.js';
import { confetti } from '../ui/confetti.js';

function miniRow(player) {
  const lead = player.is_leader;
  return html`
    <div class="mini-row player--${player.color}">
      ${avatar({ name: player.name, color: player.color, size: 40, ring: lead ? 'lead-thin' : 'none', crown: lead })}
      <div class="mini-row__main">
        <div class="mini-row__top">
          <span>${player.is_me ? 'Você' : player.name} · ${player.done} de ${player.goal}</span>
          <span class="mini-row__pts">${player.points} pts</span>
        </div>
        <div class="bar"><div class="bar__fill" style="width:${player.pct}%"></div></div>
      </div>
      <span class="mini-row__pct${lead ? ' is-lead' : ''}">${player.pct}%</span>
    </div>`;
}

export function successView({ workout, scoreboard, feedback, photoError }, { wide }) {
  const { me, opponent } = splitPlayers(scoreboard);
  const tie = opponent && me.pct === opponent.pct && me.done > 0;
  return html`
    <div class="success">
      <div class="success__content">
        <div class="success__badge">
          ${confetti({ wide })}
          <div class="success__check">${icon('check', 54, { stroke: 3 })}</div>
        </div>
        <h2 class="success__title display" id="checkin-title">+${workout.points} pontos!</h2>
        <p class="success__msg">${feedback.message}</p>
        <p class="success__summary">${workout.type} · ${workout.duration_min} min · ${workout.intensity} · ${dayLabel(workout.date, scoreboard.today)}${workout.has_photo ? ' · com foto' : ''}</p>
        ${photoError && html`
          <div class="success__photo-error" role="alert">
            ${icon('alert', 18, { stroke: 2.2 })}
            <span><strong>A foto não foi enviada.</strong> ${photoError} O treino está salvo, sem o bônus de foto.</span>
            <button class="btn btn--secondary btn--sm" type="button" data-action="retry-photo">Tentar de novo</button>
          </div>`}
        <div class="success__board">
          ${scoreboard.players.map(miniRow)}
          ${tie && html`<p class="success__tie">Meta empatada. No empate, vence quem soma mais pontos.</p>`}
        </div>
        <div class="success__pill">${icon('fire', 18)}${feedback.pill}</div>
      </div>
      <div class="success__actions">
        <button class="btn btn--secondary only-desktop" type="button" data-action="history">Ver histórico</button>
        <button class="btn btn--primary" type="button" data-action="close">Voltar ao placar</button>
      </div>
    </div>`;
}
