// Temporary home: confirms the session works. Replaced by the scoreboard in the next step.
import { api } from '../core/api.js';
import { html, on, renderInto } from '../core/dom.js';
import { go } from '../core/router.js';
import { session } from '../core/session.js';

export async function mount(root) {
  const user = session.user || (await api.me());
  session.setUser(user);
  renderInto(root, html`
    <main style="padding:72px 28px">
      <h1>Olá, ${user.first_name}</h1>
      <button class="btn btn--secondary" data-action="logout" style="margin-top:24px;padding:0 24px">Sair</button>
    </main>`);
  on(root, 'click', '[data-action="logout"]', () => { session.clear(); go('login'); });
}
