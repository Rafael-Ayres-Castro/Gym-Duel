// Screen header used by the phase 2 screens: small kicker, big Anton title and an optional action.
import { html } from '../core/dom.js';

export const pageHead = ({ kicker, title, action = '' }) => html`
  <header class="page-head">
    <div class="page-head__titles">
      <span class="page-head__kicker">${kicker}</span>
      <h1 class="page-head__title display">${title}</h1>
    </div>
    ${action}
  </header>`;
