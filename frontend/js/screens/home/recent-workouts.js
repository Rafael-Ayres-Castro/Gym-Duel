// "Últimos treinos": the 3 newest workouts of the week, or the empty-week encouragement.
import { html } from '../../core/dom.js';
import { icon } from '../../core/icons.js';
import { workoutRow } from '../../ui/workout-row.js';

const emptyWeek = () => html`
  <div class="recent__empty">
    <div class="recent__empty-icon">${icon('fire', 30)}</div>
    <div>
      <div class="recent__empty-title">Semana nova, placar zerado</div>
      <p class="recent__empty-text">Ninguém treinou ainda. Um check-in hoje já coloca você no placar e mantém sua sequência viva.</p>
    </div>
  </div>`;

export function recentWorkouts(workouts, todayIso) {
  const hasWorkouts = workouts.length > 0;
  return html`
    <section class="recent">
      <div class="recent__head">
        <h2>Últimos treinos</h2>
        <button class="link-btn recent__link${hasWorkouts ? '' : ' only-desktop'}" type="button" data-action="go-history">
          <span class="only-mobile">Ver tudo</span><span class="only-desktop">Ver histórico</span>
        </button>
      </div>
      ${hasWorkouts
        ? html`<div class="recent__list">${workouts.map((w) => workoutRow(w, todayIso))}</div>`
        : emptyWeek()}
    </section>`;
}
