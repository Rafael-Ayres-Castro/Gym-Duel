// Prêmios: balances, the store (redeem / create rewards) and the redemption cycle.
import { api, ApiError } from '../../core/api.js';
import { loadScoreboard } from '../../core/app-state.js';
import { on, renderInto } from '../../core/dom.js';
import { emit, EVENTS, listen } from '../../core/events.js';
import { session } from '../../core/session.js';
import { calcPoints } from '../../domain/rules.js';
import { showToast } from '../../ui/toast.js';
import { openCreateReward, openRedeem } from './reward-sheets.js';
import { rewardsView } from './rewards-view.js';

const otherColor = (color) => (color === 'blue' ? 'pink' : 'blue');

/** "uma semana com a meta batida rende cerca de N pts": your goal × a typical 45 min workout. */
function weekReference(rules, goal) {
  return Math.round((goal * calcPoints(45, 'Moderada', false, rules)) / 5) * 5;
}

export async function mount(container, { tab: initialTab = 'store' } = {}) {
  let active = true;
  let tab = initialTab;
  let data = null; // { store, list, pendingCount, rules }

  const render = () => {
    const me = session.user;
    const store = { ...data.store, myColor: me.color, opponentColor: otherColor(me.color) };
    renderInto(container, rewardsView({ store, me, tab, list: data.list, pendingCount: data.pendingCount }));
  };

  const refresh = async () => {
    const [store, toFulfill, list, board] = await Promise.all([
      api.store(),
      api.redemptions('to_fulfill'),
      tab === 'store' ? Promise.resolve([]) : api.redemptions(tab),
      loadScoreboard(),
    ]);
    if (!active) return;
    data = { store, list, pendingCount: toFulfill.filter((r) => r.status === 'pending').length, rules: board.rules };
    render();
  };
  await refresh();

  async function run(task, message) {
    try {
      await task();
      showToast(message);
      await refresh();
      emit(EVENTS.accountChanged);
    } catch (error) {
      if (!(error instanceof ApiError)) throw error;
      showToast(error.message);
    }
  }

  const duoName = () => data.store.opponent_name || 'Sua dupla';
  const findRedemption = (id) => data.list.find((r) => r.id === Number(id));

  const actions = {
    redeem: (target) => {
      const reward = data.store.offered_to_me.find((r) => r.id === Number(target.dataset.id));
      openRedeem({
        reward,
        balance: data.store.balance,
        duoName: duoName(),
        onRedeemed: () => { refresh(); emit(EVENTS.accountChanged); },
        onSeeMine: () => { tab = 'mine'; refresh(); },
      });
    },
    'new-reward': () => openCreateReward({
      duoName: duoName(),
      costs: data.store.costs,
      weekRef: weekReference(data.rules, session.user.weekly_goal),
      onCreated: () => { showToast(`Prêmio adicionado à loja de ${duoName()}.`); refresh(); },
    }),
    remind: (target) => run(() => api.remind(target.dataset.id), `Lembrete enviado para ${findRedemption(target.dataset.id).owner_name}.`),
    receive: (target) => run(() => api.receive(target.dataset.id), 'Prêmio marcado como recebido.'),
    fulfill: (target) => run(() => api.fulfill(target.dataset.id),
      `Pronto! ${findRedemption(target.dataset.id).redeemer_name} recebeu o aviso de que você cumpriu.`),
  };

  const offClick = on(container, 'click', '[data-tab], [data-action]', (_, target) => {
    if (target.dataset.tab) {
      tab = target.dataset.tab;
      refresh();
      return;
    }
    actions[target.dataset.action]?.(target);
  });
  const offSaved = listen(EVENTS.workoutSaved, refresh);
  return () => { active = false; offClick(); offSaved(); };
}
