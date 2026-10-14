// Player avatar: initial over the player's color. The leader gets crown, yellow ring and "LÍDER" badge.
import { html } from '../core/dom.js';
import { icon } from '../core/icons.js';
import { initial } from '../domain/format.js';

/**
 * @param {object} o
 * @param {string} o.name       player name (first letter is shown)
 * @param {string} [o.color]    "blue" | "pink"; omitted = neutral placeholder
 * @param {number} [o.size]     px; omit to let CSS size it per breakpoint
 * @param {'none'|'ring'|'lead'|'lead-thin'} [o.ring]
 * @param {boolean} [o.crown]   show the crown above
 * @param {boolean} [o.badge]   show the "LÍDER" badge below
 * @param {string} [o.cls]      extra classes
 * @param {string} [o.text]     override the letter (e.g. "?")
 */
export function avatar({ name, color, size, ring = 'none', crown = false, badge = false, cls = '', text }) {
  const classes = ['avatar', color && `player--${color}`, ring !== 'none' && `avatar--${ring === 'ring' ? 'ringed' : ring}`, cls]
    .filter(Boolean)
    .join(' ');
  return html`
    <div class="${classes}"${size ? html` style="--size:${size}px"` : ''}>
      ${crown && icon('crown', 24, { cls: 'avatar__crown' })}
      <div class="avatar__circle">${text ?? initial(name)}</div>
      ${badge && html`<span class="avatar__badge">LÍDER</span>`}
    </div>`;
}
