// App-wide events, so screens, the check-in modal and keyboard shortcuts don't import each other.

export const EVENTS = {
  openCheckin: 'gymduel:open-checkin',
  workoutSaved: 'gymduel:workout-saved',
  // Something changed the balance, goals or rules: the shell refreshes the user card.
  accountChanged: 'gymduel:account-changed',
};

export const emit = (name, detail) => window.dispatchEvent(new CustomEvent(name, { detail }));

export function listen(name, handler) {
  const listener = (event) => handler(event.detail);
  window.addEventListener(name, listener);
  return () => window.removeEventListener(name, listener);
}
