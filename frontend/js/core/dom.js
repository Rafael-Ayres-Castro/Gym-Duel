// Tiny templating: `html` escapes every interpolated value unless it is already SafeHtml.
// This keeps user content (names, notes) from ever being parsed as markup.

export class SafeHtml {
  constructor(value) { this.value = value; }
  toString() { return this.value; }
}

/** Mark a trusted string (e.g. an SVG icon) as HTML. Never pass user input here. */
export const raw = (value) => new SafeHtml(value);

const ESCAPES = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
export const escapeHtml = (value) => String(value).replace(/[&<>"']/g, (c) => ESCAPES[c]);

function toHtml(value) {
  if (value == null || value === false || value === true) return '';
  if (value instanceof SafeHtml) return value.value;
  if (Array.isArray(value)) return value.map(toHtml).join('');
  return escapeHtml(value);
}

export function html(strings, ...values) {
  let out = strings[0];
  values.forEach((value, i) => { out += toHtml(value) + strings[i + 1]; });
  return new SafeHtml(out);
}

/** Replace an element's content with a template result. */
export function renderInto(element, view) {
  element.innerHTML = toHtml(view);
  return element;
}

/** Build a detached element from a template (first element child). */
export function createElement(view) {
  const template = document.createElement('template');
  template.innerHTML = toHtml(view).trim();
  return template.content.firstElementChild;
}

/** Delegated event listener: runs `handler(event, matchedElement)` for descendants matching `selector`. */
export function on(root, type, selector, handler) {
  const listener = (event) => {
    const target = event.target.closest(selector);
    if (target && root.contains(target)) handler(event, target);
  };
  root.addEventListener(type, listener);
  return () => root.removeEventListener(type, listener);
}

export const cx = (...classes) => classes.filter(Boolean).join(' ');
