// Markup of the history screen: title + filters + summary of both players, then workouts by day.
import { html } from '../../core/dom.js';
import { icon } from '../../core/icons.js';
import { dayLabel, monthSoFar, weekRange, workoutsLabel } from '../../domain/format.js';
import { avatar } from '../../ui/avatar.js';
import { workoutRow } from '../../ui/workout-row.js';

export const PERIODS = [
  { value: 'week', label: 'Semana' },
  { value: 'month', label: 'Mês' },
];

/** Person filter; the third option is the duo's first name ("Ela" in the mockup, but it works for both). */
export const personOptions = (opponentName) => [
  { value: 'all', label: 'Todos' },
  { value: 'me', label: 'Eu' },
  { value: 'opponent', label: opponentName || 'Dupla', disabled: !opponentName },
];

const segmented = (name, options, current) => html`
  <div class="segmented history__seg history__seg--${name}" role="group">
    ${options.map((option) => html`
      <button class="segmented__btn${option.value === current ? ' is-on' : ''}" type="button"
        data-filter="${name}" data-value="${option.value}" aria-pressed="${option.value === current}"
        ${option.disabled ? html`disabled` : ''}>${option.label}</button>`)}
  </div>`;

function summaryCard(player, showGoal) {
  return html`
    <div class="sum-card player--${player.color}">
      ${avatar({ name: player.name, color: player.color, cls: 'sum-card__avatar' })}
      <span class="sum-card__name">${player.name}</span>
      <span class="sum-card__pts">${player.points} pts</span>
      <div class="sum-card__count"><span class="sum-card__num">${player.workouts}</span> ${workoutsLabel(player.workouts)}</div>
      ${showGoal && html`
        <div class="sum-card__goal only-desktop">
          <div class="bar"><div class="bar__fill" style="width:${player.pct}%"></div></div>
          <span>${player.pct}% da meta</span>
        </div>`}
    </div>`;
}

/** Group workouts (already newest first) by day. */
function byDay(workouts) {
  const groups = [];
  workouts.forEach((workout) => {
    const last = groups[groups.length - 1];
    if (last?.date === workout.date) last.items.push(workout);
    else groups.push({ date: workout.date, items: [workout] });
  });
  return groups;
}

const dayGroup = (group, todayIso) => html`
  <section class="day-group">
    <div class="day-group__head">
      <span>${dayLabel(group.date, todayIso, { long: true })}</span>
      <span>+${group.items.reduce((total, w) => total + w.points, 0)} pts</span>
    </div>
    <div class="day-group__list">${group.items.map((w) => workoutRow(w, todayIso, { showWhen: false, showNote: true }))}</div>
  </section>`;

export function historyView({ board, summary, workouts, filters, opponentName }) {
  const isWeek = filters.period === 'week';
  const range = weekRange(board.week_start, board.week_end);
  return html`
    <div class="history">
      <header class="history__top">
        <div class="history__titles">
          <span class="history__period">${isWeek ? html`<span class="only-desktop">Semana de </span>${range}` : monthSoFar(board.today)}</span>
          <h1 class="history__title display">Histórico</h1>
        </div>
        <div class="history__filters">
          ${segmented('person', personOptions(opponentName), filters.person)}
          ${segmented('period', PERIODS, filters.period)}
          <button class="btn btn--primary history__checkin only-desktop" type="button" data-action="open-checkin">
            ${icon('plus', 18, { stroke: 2.6 })}Fiz check-in
          </button>
        </div>
        <div class="history__summary">${summary.players.map((player) => summaryCard(player, isWeek))}</div>
      </header>
      <div class="history__list">
        ${workouts.length
          ? byDay(workouts).map((group) => dayGroup(group, board.today))
          : html`<p class="history__empty">Nenhum treino neste período ainda. O primeiro check-in aparece aqui.</p>`}
      </div>
    </div>`;
}
