// Histórico: workouts of both players with Todos/Eu/Dupla and Semana/Mês filters.
import { api } from '../../core/api.js';
import { loadScoreboard } from '../../core/app-state.js';
import { on, renderInto } from '../../core/dom.js';
import { emit, EVENTS, listen } from '../../core/events.js';
import { splitPlayers } from '../../domain/players.js';
import { historyView } from './history-view.js';

export async function mount(container) {
  let active = true;
  // Every visit starts on "Todos · Semana", like the prototype's "Ver histórico".
  const filters = { person: 'all', period: 'week' };

  const refresh = async () => {
    const [board, summary, workouts] = await Promise.all([
      loadScoreboard(),
      api.summary(filters.period),
      api.workouts({ person: filters.person, period: filters.period }),
    ]);
    if (!active) return;
    const { opponent } = splitPlayers(board);
    renderInto(container, historyView({ board, summary, workouts, filters, opponentName: opponent?.name }));
  };
  await refresh();

  const offClick = on(container, 'click', '[data-filter], [data-action]', (_, target) => {
    if (target.dataset.action === 'open-checkin') return emit(EVENTS.openCheckin);
    const { filter, value } = target.dataset;
    if (filters[filter] === value) return;
    filters[filter] = value;
    refresh();
  });
  const offSaved = listen(EVENTS.workoutSaved, refresh);
  return () => { active = false; offClick(); offSaved(); };
}
