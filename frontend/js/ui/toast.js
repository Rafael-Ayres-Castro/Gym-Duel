// Short confirmation message at the bottom of the screen (2.6 s, like the prototype).
import { createElement, html } from '../core/dom.js';
import { icon } from '../core/icons.js';

let element = null;
let timer = null;

export function showToast(message) {
  clearTimeout(timer);
  element?.remove();
  element = createElement(html`<div class="toast" role="status">${icon('trophy', 18, { stroke: 2.2 })}${message}</div>`);
  document.body.append(element);
  timer = setTimeout(() => { element?.remove(); element = null; }, 2600);
}
