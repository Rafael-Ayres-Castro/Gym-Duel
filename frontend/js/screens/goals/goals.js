// Metas e regras: change your weekly goal (from next week on), see streaks and badges,
// and propose / approve scoring rule changes with your duo.
import { api, ApiError } from '../../core/api.js';
import { loadScoreboard } from '../../core/app-state.js';
import { on, renderInto } from '../../core/dom.js';
import { emit, EVENTS, listen } from '../../core/events.js';
import { session } from '../../core/session.js';
import { addDays, dayMonth, parseDate } from '../../domain/format.js';
import { MAX_GOAL, MIN_GOAL } from '../../domain/rules.js';
import { showToast } from '../../ui/toast.js';
import { goalsView } from './goals-view.js';

const sameRules = (a, b) => Object.keys(a).every((key) => a[key] === b[key]);

export async function mount(container) {
  let active = true;
  let data = null; // server data: me, board, streaks, rules
  const local = { goalDraft: null, rulesDraft: null }; // unsaved edits

  /** Everything the view needs: server data plus the unsaved edits. */
  function state() {
    const opponent = data.board.players.find((p) => !p.is_me);
    const baseGoal = data.me.next_weekly_goal ?? data.me.weekly_goal;
    const goalDraft = local.goalDraft ?? baseGoal;
    // While a proposal is pending, the rows show the proposed values (read-only).
    const rulesDraft = data.rules.pending?.values ?? local.rulesDraft ?? data.rules.current;
    return {
      ...data,
      goalDraft,
      goalChanged: goalDraft !== baseGoal,
      rulesDraft,
      rulesDirty: !data.rules.pending && !sameRules(rulesDraft, data.rules.current),
      rulesLocked: Boolean(data.rules.pending) || !opponent,
      hasOpponent: Boolean(opponent),
      opponentName: opponent?.name || 'sua dupla',
    };
  }

  const render = () => renderInto(container, goalsView(state()));

  const refresh = async () => {
    const [me, board, streaks, rules] = await Promise.all([api.me(), loadScoreboard(), api.streaks(), api.rules()]);
    session.setUser(me);
    if (!active) return;
    data = { me, board, streaks, rules };
    render();
  };
  await refresh();

  async function run(task, successMessage) {
    try {
      await task();
      if (successMessage) showToast(successMessage);
      local.rulesDraft = null;
      await refresh();
      emit(EVENTS.accountChanged);
    } catch (error) {
      if (!(error instanceof ApiError)) throw error;
      showToast(error.message);
    }
  }

  async function saveGoal() {
    const goal = state().goalDraft;
    const nextMonday = addDays(parseDate(data.board.week_start), 7);
    await run(() => api.updateMe({ weekly_goal: goal }),
      goal === data.me.weekly_goal ? 'Meta mantida.' : `Meta salva: ${goal} treinos a partir de ${dayMonth(nextMonday)}.`);
    local.goalDraft = null;
    render();
  }

  const actions = {
    'goal-dec': () => { local.goalDraft = Math.max(MIN_GOAL, state().goalDraft - 1); render(); },
    'goal-inc': () => { local.goalDraft = Math.min(MAX_GOAL, state().goalDraft + 1); render(); },
    'goal-reset': () => { local.goalDraft = null; render(); },
    'goal-save': saveGoal,
    'rules-discard': () => { local.rulesDraft = null; render(); },
    'rules-propose': () => run(() => api.proposeRules(state().rulesDraft), `Proposta enviada para ${state().opponentName}.`),
    'rules-cancel': () => run(() => api.cancelRules(data.rules.pending.id), 'Proposta cancelada.'),
    'rules-approve': () => run(() => api.approveRules(data.rules.pending.id), 'Regras aprovadas pelos dois. Pontos recalculados.'),
    'rules-reject': () => run(() => api.rejectRules(data.rules.pending.id), 'Proposta recusada. As regras atuais continuam valendo.'),
  };

  const offClick = on(container, 'click', '[data-action], [data-rule]', (_, target) => {
    if (target.dataset.rule) {
      local.rulesDraft = { ...state().rulesDraft, [target.dataset.rule]: Number(target.dataset.value) };
      render();
      return;
    }
    actions[target.dataset.action]?.();
  });
  const offSaved = listen(EVENTS.workoutSaved, refresh);
  return () => { active = false; offClick(); offSaved(); };
}
