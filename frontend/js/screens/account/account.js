// Minha conta: profile, points and achievements, edit name / e-mail / password,
// switch between accounts saved on this device and log out.
import { api } from '../../core/api.js';
import { on, renderInto } from '../../core/dom.js';
import { emit, EVENTS, listen } from '../../core/events.js';
import { go } from '../../core/router.js';
import { session } from '../../core/session.js';
import { addAccount, logout, switchAccount } from '../../layout/app-shell.js';
import { showToast } from '../../ui/toast.js';
import { openEditEmail, openEditName, openEditPassword } from './account-sheets.js';
import { accountView } from './account-view.js';

export async function mount(container) {
  let active = true;
  let data = null; // { me, stats }

  const refresh = async () => {
    const [me, stats] = await Promise.all([api.me(), api.profileStats()]);
    session.setUser(me); // also refreshes this account's saved entry (name, e-mail)
    if (!active) return;
    data = { me, stats };
    renderInto(container, accountView({ ...data, otherAccounts: session.otherAccounts }));
  };
  await refresh();

  /** After an edit: confirm, redraw this screen and let the shell update the sidebar card. */
  const afterEdit = (message) => () => {
    showToast(message);
    refresh().catch(() => {});
    emit(EVENTS.accountChanged);
  };

  const actions = {
    'edit-name': () => openEditName(data.me, afterEdit('Nome atualizado.')),
    'edit-email': () => openEditEmail(data.me, afterEdit('E-mail atualizado. Use o novo para entrar.')),
    'edit-password': () => openEditPassword(() => showToast('Senha alterada. Use a nova no próximo login.')),
    'go-goals': () => go('goals'),
    'switch-account': (target) => switchAccount(Number(target.dataset.accountId)),
    'add-account': addAccount,
    'account-logout': logout,
  };
  const offClick = on(container, 'click', '[data-action]', (_, target) => actions[target.dataset.action]?.(target));
  const offSaved = listen(EVENTS.workoutSaved, refresh);
  return () => { active = false; offClick(); offSaved(); };
}
