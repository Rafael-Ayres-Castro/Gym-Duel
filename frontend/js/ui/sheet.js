// Generic dialog: a sheet that slides up on mobile, a centered modal on desktop.
// Esc and a click on the dimmed backdrop close it; focus returns to where it was.
import { createElement, html, on, renderInto } from '../core/dom.js';
import { icon } from '../core/icons.js';

/** Standard sheet header: title, subtitle and the close button. */
export const sheetHead = (title, subtitle) => html`
  <header class="sheet__head">
    <div>
      <h2>${title}</h2>
      <p>${subtitle}</p>
    </div>
    <button class="icon-btn" type="button" data-action="close-sheet" aria-label="Fechar">${icon('close', 18, { stroke: 2.4 })}</button>
  </header>`;

/**
 * @param {SafeHtml} view          content
 * @param {object} options
 * @param {string} options.label   accessible name of the dialog
 * @param {'sm'|'md'|'lg'} [options.size]
 * @param {(action: string, el: HTMLElement) => void} [options.onAction]  clicks on [data-action]
 * @param {() => void} [options.onClose]
 * @returns {{ element: HTMLElement, close: () => void, update: (view) => void }}
 */
export function openSheet(view, { label, size = 'md', onAction, onClose } = {}) {
  const previousFocus = document.activeElement;
  const overlay = createElement(html`
    <div class="sheet-overlay">
      <div class="sheet sheet--${size}" role="dialog" aria-modal="true" aria-label="${label}" tabindex="-1"></div>
    </div>`);
  const dialog = overlay.firstElementChild;
  renderInto(dialog, view);

  const onKeydown = (event) => {
    if (event.key === 'Escape') {
      event.preventDefault();
      close();
    }
  };
  const offAction = on(dialog, 'click', '[data-action]', (event, target) => {
    if (target.dataset.action === 'close-sheet') close();
    else onAction?.(target.dataset.action, target, event);
  });
  overlay.addEventListener('click', (event) => { if (event.target === overlay) close(); });
  document.addEventListener('keydown', onKeydown);

  let closed = false;
  function close() {
    if (closed) return;
    closed = true;
    offAction();
    document.removeEventListener('keydown', onKeydown);
    overlay.remove();
    if (!document.querySelector('.sheet-overlay, .checkin-overlay')) document.body.classList.remove('has-modal');
    previousFocus?.focus?.({ preventScroll: true });
    onClose?.();
  }

  document.body.append(overlay);
  document.body.classList.add('has-modal');
  dialog.focus({ preventScroll: true });
  return { element: dialog, close, update: (next) => renderInto(dialog, next) };
}
