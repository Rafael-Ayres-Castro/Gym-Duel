// Short confirmation message at the bottom of the screen (2.6 s, like the prototype).
// Several messages (e.g. notifications on login) are shown one after the other.
import { createElement, html } from '../core/dom.js';
import { icon } from '../core/icons.js';

const DURATION_MS = 2600;
let element = null;
let timer = null;
let queue = [];

function showNext() {
  element?.remove();
  element = null;
  const message = queue.shift();
  if (message === undefined) return;
  element = createElement(html`<div class="toast" role="status">${icon('trophy', 18, { stroke: 2.2 })}${message}</div>`);
  document.body.append(element);
  timer = setTimeout(showNext, DURATION_MS);
}

/** Show a message now, replacing whatever is on screen. */
export function showToast(message) {
  clearTimeout(timer);
  queue = [message];
  showNext();
}

/** Show messages in order, after the current one. */
export function queueToasts(messages) {
  queue.push(...messages);
  if (!element) showNext();
}
