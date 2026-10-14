// Home / placar: greeting, weekly scoreboard, big check-in button and latest workouts.
import { api } from '../../core/api.js';
import { loadScoreboard } from '../../core/app-state.js';
import { html, on, renderInto } from '../../core/dom.js';
import { emit, EVENTS, listen } from '../../core/events.js';
import { icon } from '../../core/icons.js';
import { go } from '../../core/router.js';
import { session } from '../../core/session.js';
import { greeting, weekRange } from '../../domain/format.js';
import { splitPlayers, weekIsEmpty } from '../../domain/players.js';
import { logout } from '../../layout/app-shell.js';
import { toggleAccountMenu } from '../../ui/account-menu.js';
import { avatar } from '../../ui/avatar.js';
import { recentWorkouts } from './recent-workouts.js';
import { scoreboardCard } from './scoreboard-card.js';

export const checkinButton = ({ withKey = false, cls = '' } = {}) => html`
  <button class="btn btn--primary btn-checkin ${cls}" type="button" data-action="open-checkin">
    <span class="btn-checkin__bubble">${icon('check', 18, { stroke: 3 })}</span>Fiz check-in${withKey && html`<span class="btn-checkin__key" aria-hidden="true">C</span>`}
  </button>`;

function homeView(board, recents, user) {
  const { me, opponent } = splitPlayers(board);
  return html`
    <div class="home">
      <header class="home__header">
        <div class="home__titles">
          <div class="home__week">${icon('calendar', 16, { stroke: 2.2 })}Semana de ${weekRange(board.week_start, board.week_end)}</div>
          <h1 class="home__greeting">${greeting(user.first_name, weekIsEmpty(board))}</h1>
        </div>
        <button class="home__me only-mobile" type="button" data-action="account" aria-label="Conta de ${user.first_name}">
          ${avatar({ name: user.first_name, color: user.color, size: 42 })}
        </button>
        ${checkinButton({ withKey: true, cls: 'only-desktop' })}
      </header>
      ${scoreboardCard(board, me, opponent)}
      ${checkinButton({ cls: 'home__checkin only-mobile' })}
      <div class="home__grid">
        ${recentWorkouts(recents, board.today)}
      </div>
    </div>`;
}

export async function mount(container) {
  let active = true;
  const refresh = async () => {
    const [board, recents] = await Promise.all([loadScoreboard(), api.workouts({ period: 'week', limit: 3 })]);
    if (active) renderInto(container, homeView(board, recents, session.user)); // user may have left meanwhile
  };
  await refresh();

  const offClick = on(container, 'click', '[data-action]', (_, target) => {
    const action = target.dataset.action;
    if (action === 'open-checkin') emit(EVENTS.openCheckin);
    if (action === 'go-history') go('history');
    if (action === 'account') toggleAccountMenu(target, session.user, logout);
  });
  // A check-in from the modal changes the board: fetch and render again.
  const offSaved = listen(EVENTS.workoutSaved, refresh);
  return () => { active = false; offClick(); offSaved(); };
}
