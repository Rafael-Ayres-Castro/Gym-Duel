// Desafios: answer received challenges, follow active ones (progress comes from the workouts)
// and create new ones for your duo.
import { api, ApiError } from '../../core/api.js';
import { loadScoreboard } from '../../core/app-state.js';
import { on, renderInto } from '../../core/dom.js';
import { emit, EVENTS, listen } from '../../core/events.js';
import { session } from '../../core/session.js';
import { showToast } from '../../ui/toast.js';
import { openNewChallenge } from './challenge-sheet.js';
import { challengesView } from './challenges-view.js';

export async function mount(container) {
  let active = true;
  let data = null; // { board, today, duoName }

  const refresh = async () => {
    const [board, scoreboard] = await Promise.all([api.challenges(), loadScoreboard()]);
    if (!active) return;
    const duo = scoreboard.players.find((p) => !p.is_me);
    data = { board, today: scoreboard.today, duoName: duo?.name || null };
    renderInto(container, challengesView({ board, me: session.user, duoName: data.duoName || 'Sua dupla' }));
  };
  await refresh();

  async function run(task, message) {
    try {
      await task();
      showToast(message);
      await refresh();
      emit(EVENTS.accountChanged); // updates the pink counter on the navigation
    } catch (error) {
      if (!(error instanceof ApiError)) throw error;
      showToast(error.message);
    }
  }

  const actions = {
    'new-challenge': () => {
      if (!data.duoName) return showToast('Sua dupla precisa se cadastrar para receber desafios.');
      return openNewChallenge({
        duoName: data.duoName,
        todayIso: data.today,
        onSent: () => { showToast(`Desafio enviado para ${data.duoName}.`); refresh(); },
      });
    },
    accept: (id) => run(() => api.acceptChallenge(id), 'Desafio aceito. Boa sorte!'),
    decline: (id) => run(() => api.declineChallenge(id), `Desafio recusado. ${data.duoName} recebeu um aviso.`),
    cancel: (id) => run(() => api.cancelChallenge(id), 'Desafio cancelado.'),
  };

  const offClick = on(container, 'click', '[data-action]', (_, target) => actions[target.dataset.action]?.(target.dataset.id));
  const offSaved = listen(EVENTS.workoutSaved, refresh); // a check-in moves the progress bars
  return () => { active = false; offClick(); offSaved(); };
}
