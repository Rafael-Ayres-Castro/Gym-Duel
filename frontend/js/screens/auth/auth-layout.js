// Shared frame of the login and sign up screens: hero (desktop only) + form panel.
import { html } from '../../core/dom.js';
import { icon } from '../../core/icons.js';

export const brandRow = () => html`
  <div class="brand">
    <div class="brand__logo">${icon('bolt', 24)}</div>
    <span class="brand__name">GYM <em>DUEL</em></span>
  </div>`;

/** Big mobile brand block from the login mockup (logo 64, title 60). */
export const mobileBrand = () => html`
  <div class="auth-brand only-mobile">
    <div class="brand__logo" style="--size:64px">${icon('bolt', 32)}</div>
    <div class="auth-brand__title">GYM <em>DUEL</em></div>
    <p class="auth-brand__tagline">Treinem juntos. Disputem a semana.</p>
  </div>`;

// Illustration only: a sample duel that explains the % of goal idea.
const hero = () => html`
  <section class="auth-hero only-desktop">
    ${brandRow()}
    <div class="auth-hero__body">
      <h1 class="auth-hero__title display">Treinem juntos.<br><span>Disputem a semana.</span></h1>
      <p class="auth-hero__text">Cada treino vira ponto. O placar compara a % da meta pessoal de cada um, então a disputa é justa para os dois.</p>
      <div class="auth-hero__duel" aria-hidden="true">
        <div class="auth-hero__player player--blue">
          <div class="avatar" style="--size:48px"><div class="avatar__circle">V</div></div>
          <div><div class="auth-hero__name">Você</div><div class="auth-hero__pct">75%</div></div>
        </div>
        <span class="auth-hero__vs">VS</span>
        <div class="auth-hero__player auth-hero__player--lead player--pink">
          <div class="avatar avatar--lead-thin" style="--size:48px">
            ${icon('crown', 22, { cls: 'avatar__crown' })}
            <div class="avatar__circle">D</div>
          </div>
          <div><div class="auth-hero__name">Sua dupla</div><div class="auth-hero__pct is-lead">100%</div></div>
        </div>
      </div>
    </div>
  </section>`;

export function authLayout(formView) {
  return html`
    <div class="auth">
      ${hero()}
      <main class="auth-panel">${formView}</main>
    </div>`;
}
