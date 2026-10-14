// Confetti burst in the app colors (gdBurst animation from the prototype).
// Pieces are placed on a ring; the wider desktop modal spreads them 1.5× horizontally.
import { html, raw } from '../core/dom.js';

const COLORS = ['#FFE14A', '#4C8DFF', '#FF5CA8', '#FF8A1F', '#F3F4F6'];

export function confetti({ wide = false } = {}) {
  const count = wide ? 24 : 22;
  const pieces = [];
  for (let i = 0; i < count; i += 1) {
    const angle = (i / count) * Math.PI * 2 + (i % 2 ? (wide ? 0.13 : 0.14) : 0);
    const radius = wide ? 90 + (i % 4) * 20 : 92 + (i % 4) * 17;
    const dx = Math.round(Math.cos(angle) * radius * (wide ? 1.5 : 1));
    const dy = Math.min(wide ? 70 : 78, Math.round(Math.sin(angle) * radius));
    const isStrip = i % 3 === 0;
    const [w, h] = isStrip ? [13, 5] : [8, 8];
    const style = [
      `width:${w}px`, `height:${h}px`, `margin:${-h / 2}px 0 0 ${-w / 2}px`,
      `border-radius:${isStrip ? 2 : 4}px`, `background:${COLORS[i % COLORS.length]}`,
      `--dx:${dx}px`, `--dy:${dy}px`, `--rot:${(i * 47) % 180}deg`, `animation-delay:${(i % 4) * 0.05}s`,
    ].join(';');
    pieces.push(`<span class="confetti__piece" style="${style}"></span>`);
  }
  return html`<div class="confetti" aria-hidden="true">${raw(pieces.join(''))}</div>`;
}
