// Button for an account saved on this device ("Continuar como…"): avatar, name, e-mail and a chevron.
import { html } from '../core/dom.js';
import { icon } from '../core/icons.js';
import { avatar } from './avatar.js';

/** `account` comes from session.otherAccounts; clicks carry data-action and data-account-id. */
export const savedAccountButton = (account, action) => html`
  <button class="saved-account" type="button" data-action="${action}" data-account-id="${account.id}">
    ${avatar({ name: account.firstName, color: account.color, size: 40 })}
    <span class="saved-account__text">
      <span class="saved-account__name">${account.firstName}</span>
      <span class="saved-account__email">${account.email}</span>
    </span>
    ${icon('chevronRight', 20, { stroke: 2.4, cls: 'saved-account__chevron' })}
  </button>`;
