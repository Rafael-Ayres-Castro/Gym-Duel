// Markup of "Minha conta": profile, points, all-time achievements, account data and the
// accounts saved on this device.
import { html } from '../../core/dom.js';
import { icon } from '../../core/icons.js';
import { durationParts, monthYear, plural } from '../../domain/format.js';
import { avatar } from '../../ui/avatar.js';
import { pageHead } from '../../ui/page-head.js';
import { savedAccountButton } from '../../ui/saved-account.js';

const COLOR_NAMES = { blue: 'azul', pink: 'rosa' };

// The real password is never known by the app (only its bcrypt hash is stored), so it is masked.
const PASSWORD_MASK = '••••••••';

function profileCard(me) {
  return html`
    <section class="profile-card player--${me.color}">
      ${avatar({ name: me.first_name, color: me.color, size: 72, ring: 'ring' })}
      <div class="profile-card__text">
        <h2 class="profile-card__name">${me.name}</h2>
        <p class="profile-card__email">${me.email}</p>
        <p class="profile-card__since">No Gym Duel desde ${monthYear(me.created_at)} · jogador ${COLOR_NAMES[me.color]}</p>
      </div>
    </section>`;
}

// ---- Numbers ----

const statTile = ({ label, value, unit = '', note = '', tone = '' }) => html`
  <div class="stat-tile${tone ? ` stat-tile--${tone}` : ''}">
    <span class="stat-tile__label">${label}</span>
    <span class="stat-tile__value"><span class="display">${value}</span>${unit && html`<small>${unit}</small>`}</span>
    ${note && html`<span class="stat-tile__note">${note}</span>`}
  </div>`;

function pointsCard(me, stats) {
  const redeemed = stats.rewards_redeemed;
  return html`
    <section class="panel-card account-card account-card--points">
      <div class="panel-card__head">
        <h2>Pontos</h2>
        <p>O saldo acumula para sempre. O placar zera toda semana.</p>
      </div>
      <div class="stat-grid stat-grid--3">
        ${statTile({ label: 'Saldo', value: me.balance, unit: 'pts', tone: 'accent', note: 'para gastar na loja' })}
        ${statTile({ label: 'Ganhos', value: stats.points_earned, unit: 'pts', note: 'treinos e bônus' })}
        ${statTile({ label: 'Gastos', value: stats.points_spent, unit: 'pts', note: `${redeemed} ${plural(redeemed, 'prêmio', 'prêmios')}` })}
      </div>
    </section>`;
}

function achievementsCard(stats) {
  const time = durationParts(stats.minutes);
  const weeks = (count) => plural(count, 'semana', 'semanas');
  return html`
    <section class="panel-card account-card account-card--achievements">
      <div class="panel-card__head">
        <h2>Conquistas</h2>
        <p>Tudo desde o cadastro.</p>
      </div>
      <div class="stat-grid">
        ${statTile({ label: 'Treinos', value: stats.workouts })}
        ${statTile({ label: 'Tempo treinando', value: time.value, unit: time.unit })}
        ${statTile({ label: 'Semanas vencidas', value: stats.weeks_won, unit: `de ${stats.weeks_closed}` })}
        ${statTile({ label: 'Metas batidas', value: stats.weeks_goal_met, unit: weeks(stats.weeks_goal_met) })}
        ${statTile({ label: 'Sequência', value: stats.streak, unit: weeks(stats.streak), tone: stats.streak ? 'fire' : '' })}
        ${statTile({ label: 'Recorde', value: stats.record, unit: weeks(stats.record) })}
        ${statTile({ label: 'Selos', value: stats.badges })}
        ${statTile({ label: 'Desafios vencidos', value: stats.challenges_won })}
      </div>
      ${stats.favorite_type && html`
        <p class="account-card__note">${icon('trophy', 16, { stroke: 2.2 })}Modalidade favorita: <strong>${stats.favorite_type}</strong></p>`}
    </section>`;
}

// ---- Account data ----

const dataRow = ({ label, value, sub = '', action, button = 'Alterar' }) => html`
  <div class="data-row">
    <div class="data-row__text">
      <span class="data-row__label">${label}</span>
      <span class="data-row__value">${value}</span>
      ${sub && html`<span class="data-row__sub">${sub}</span>`}
    </div>
    <button class="btn btn--secondary btn--xs" type="button" data-action="${action}">${button}</button>
  </div>`;

function goalSub(me) {
  return me.next_weekly_goal ? `Passa a ${me.next_weekly_goal} na próxima semana` : '';
}

function dataCard(me) {
  return html`
    <section class="panel-card account-card account-card--data">
      <div class="panel-card__head"><h2>Dados da conta</h2></div>
      <div class="data-rows">
        ${dataRow({ label: 'Nome', value: me.name, action: 'edit-name' })}
        ${dataRow({ label: 'E-mail', value: me.email, sub: 'Usado para entrar no app', action: 'edit-email' })}
        ${dataRow({ label: 'Senha', value: PASSWORD_MASK, action: 'edit-password' })}
        ${dataRow({ label: 'Meta semanal', value: `${me.weekly_goal} ${plural(me.weekly_goal, 'treino', 'treinos')} por semana`, sub: goalSub(me), action: 'go-goals', button: 'Ajustar' })}
      </div>
    </section>`;
}

// ---- Accounts on this device ----

function deviceCard(otherAccounts) {
  return html`
    <section class="panel-card account-card account-card--device">
      <div class="panel-card__head">
        <h2>Trocar de conta</h2>
        <p>Contas já conectadas neste aparelho entram sem digitar a senha. "Sair" remove a conta daqui.</p>
      </div>
      ${otherAccounts.length > 0 && html`
        <div class="saved-accounts">${otherAccounts.map((account) => savedAccountButton(account, 'switch-account'))}</div>`}
      <div class="account-card__actions">
        <button class="btn btn--secondary btn--sm" type="button" data-action="add-account">${icon('swap', 18, { stroke: 2.2 })}Entrar com outra conta</button>
        <button class="btn btn--ghost btn--sm account-logout" type="button" data-action="account-logout">${icon('logout', 18)}Sair desta conta</button>
      </div>
    </section>`;
}

export function accountView({ me, stats, otherAccounts }) {
  return html`
    <div class="account">
      ${pageHead({ kicker: 'Perfil, pontos e configurações', title: 'Minha conta' })}
      <div class="account__grid">
        ${profileCard(me)}
        ${pointsCard(me, stats)}
        ${achievementsCard(stats)}
        ${dataCard(me)}
        ${deviceCard(otherAccounts)}
      </div>
    </div>`;
}
