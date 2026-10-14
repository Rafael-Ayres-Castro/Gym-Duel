// One workout line: avatar, type, "Ana · 45 min · Alta", points and (optionally) the day.
import { html } from '../core/dom.js';
import { dayLabel } from '../domain/format.js';
import { avatar } from './avatar.js';

export function workoutRow(workout, todayIso, { showWhen = true, showNote = false } = {}) {
  return html`
    <div class="wrow">
      ${avatar({ name: workout.user_name, color: workout.color, cls: 'wrow__avatar' })}
      <div class="wrow__main">
        <div class="wrow__type">${workout.type}</div>
        <div class="wrow__meta">${workout.user_name} · ${workout.duration_min} min · ${workout.intensity}</div>
        ${showNote && workout.note && html`<div class="wrow__note">“${workout.note}”</div>`}
      </div>
      <div class="wrow__end">
        <span class="wrow__pts">+${workout.points} pts</span>
        ${showWhen && html`<span class="wrow__when">${dayLabel(workout.date, todayIso)}</span>`}
      </div>
    </div>`;
}
