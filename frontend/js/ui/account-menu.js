// Small menu under the mobile avatar: who is logged in, their goal and "Sair".
// (On desktop the same info lives in the sidebar user card.)
import { createElement, html } from '../core/dom.js';
import { icon } from '../core/icons.js';

let openMenu = null;

export function closeAccountMenu() {
  openMenu?.remove();
  openMenu = null;
  document.removeEventListener('pointerdown', onOutside, true);
  document.removeEventListener('keydown', onEscape, true);
}

function onOutside(event) {
  if (openMenu && !openMenu.contains(event.target) && !event.target.closest('[data-action="account"]')) closeAccountMenu();
}
function onEscape(event) {
  if (event.key === 'Escape') closeAccountMenu();
}

export function toggleAccountMenu(anchor, user, onLogout) {
  if (openMenu) return closeAccountMenu();
  openMenu = createElement(html`
    <div class="account-menu" role="menu">
      <div class="account-menu__who">
        <strong>${user.name}</strong>
        <span>Meta: ${user.weekly_goal} treinos/semana</span>
      </div>
      <button class="account-menu__item" role="menuitem" type="button">${icon('logout', 18)} Sair</button>
    </div>`);
  openMenu.querySelector('button').addEventListener('click', () => { closeAccountMenu(); onLogout(); });
  const box = anchor.getBoundingClientRect();
  openMenu.style.top = `${box.bottom + window.scrollY + 8}px`;
  openMenu.style.right = `${document.documentElement.clientWidth - box.right}px`;
  document.body.append(openMenu);
  document.addEventListener('pointerdown', onOutside, true);
  document.addEventListener('keydown', onEscape, true);
}
