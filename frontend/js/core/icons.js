// SVG icons copied from the design (24×24 viewBox). Stroke icons inherit currentColor.
import { raw } from './dom.js';

const STROKE = {
  mail: '<rect x="3" y="5" width="18" height="14" rx="3"/><path d="M4 7l8 6 8-6"/>',
  alert: '<circle cx="12" cy="12" r="9"/><path d="M12 7.5v5.5M12 16.5v.01"/>',
  lock: '<rect x="4.5" y="10.5" width="15" height="10" rx="2.5"/><path d="M8 10.5V7.5a4 4 0 0 1 8 0v3"/>',
  eye: '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/><circle cx="12" cy="12" r="3"/>',
  home: '<path d="M4 10.5 12 4l8 6.5V19a1 1 0 0 1-1 1h-4.5v-5.5h-5V20H5a1 1 0 0 1-1-1z"/>',
  history: '<path d="M3.5 12a8.5 8.5 0 1 0 2.6-6.1L3.5 8.5"/><path d="M3.5 4v4.5H8"/><path d="M12 7.5V12l3 2"/>',
  trophy: '<path d="M8 4h8v5a4 4 0 0 1-8 0z"/><path d="M16 5.5h3V7a3 3 0 0 1-3 3M8 5.5H5V7a3 3 0 0 0 3 3M12 13v4M8.5 20h7"/>',
  user: '<circle cx="12" cy="8.5" r="3.8"/><path d="M4.5 20a7.5 7.5 0 0 1 15 0"/>',
  logout: '<path d="M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3"/><path d="M10 16l-4-4 4-4M6 12h10"/>',
  calendar: '<rect x="3.5" y="5" width="17" height="15.5" rx="3"/><path d="M3.5 10h17M8 3v4M16 3v4"/>',
  check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  close: '<path d="M6 6l12 12M18 6 6 18"/>',
};

const FILL = {
  bolt: '<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>',
  crown: '<path d="M3 8l4.5 3.5L12 5l4.5 6.5L21 8l-1.8 10H4.8z"/>',
  fire: '<path d="M12 2.5c.6 3.2 2.6 5 4.3 6.9 1.6 1.8 2.7 3.6 2.7 6.1A7 7 0 0 1 5 15.5c0-2.3 1-4.1 2.6-5.6.3 1.6 1.2 2.7 2.4 3.2-.6-3.8.4-7.6 2-10.6z"/>',
};

/**
 * @param {string} name   icon name
 * @param {number} size   width/height in px
 * @param {object} [opts] { stroke: stroke width, cls: extra class }
 */
export function icon(name, size = 20, { stroke = 2, cls = '' } = {}) {
  const isFill = name in FILL;
  const body = isFill ? FILL[name] : STROKE[name];
  if (!body) throw new Error(`Unknown icon: ${name}`);
  const kind = isFill ? 'i-fill' : 'i-stroke';
  const strokeAttr = isFill ? '' : ` stroke-width="${stroke}"`;
  return raw(
    `<svg class="${kind} ${cls}" width="${size}" height="${size}" viewBox="0 0 24 24"${strokeAttr} aria-hidden="true">${body}</svg>`,
  );
}
