// Desktop shortcut: "C" opens the check-in from Home or Histórico (Enter/Esc live in the modal).
import { emit, EVENTS } from './events.js';
import { currentRouteName } from './router.js';

const SCREENS_WITH_CHECKIN = new Set(['home', 'history', 'challenges', 'rewards', 'goals']);

function onKeydown(event) {
  if (event.key !== 'c' && event.key !== 'C') return;
  if (event.metaKey || event.ctrlKey || event.altKey || event.repeat) return;
  if (event.target.closest?.('input, textarea, select, [contenteditable="true"]')) return;
  if (document.body.classList.contains('has-modal')) return;
  if (!SCREENS_WITH_CHECKIN.has(currentRouteName())) return;
  event.preventDefault();
  emit(EVENTS.openCheckin);
}

export function initShortcuts() {
  document.addEventListener('keydown', onKeydown);
}
