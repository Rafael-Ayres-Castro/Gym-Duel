// Regras: explains how points, the weekly leader, streaks and check-ins work.
import { api } from '../../core/api.js';
import { renderInto } from '../../core/dom.js';
import { session } from '../../core/session.js';
import { rulesView } from './rules-view.js';

export async function mount(container) {
  const rules = await api.rules();
  renderInto(container, rulesView(rules, session.user));
}
