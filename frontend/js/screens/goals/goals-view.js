// Markup of "Metas e regras" (prototype v2): weekly goals, streaks with badges and the scoring rules.
import { html } from '../../core/dom.js';
import { icon } from '../../core/icons.js';
import { addDays, dayMonth, parseDate, plural, toIso, weekRange } from '../../domain/format.js';
import { calcPoints, MAX_GOAL, MIN_GOAL } from '../../domain/rules.js';
import { avatar } from '../../ui/avatar.js';
import { pageHead } from '../../ui/page-head.js';

// Labels of each rule and its options, as in the prototype.
export const RULE_DEFS = [
  { key: 'minutes_per_point', label: 'Pontos por tempo', desc: '1 ponto a cada X minutos de treino', format: (v) => `${v} min` },
  { key: 'intensity_adjust', label: 'Intensidade', desc: 'Quanto o treino leve tira e o alto soma', format: (v) => `±${v}` },
  { key: 'photo_bonus', label: 'Foto como prova', desc: 'Bônus por treino registrado com foto', format: (v) => `+${v}` },
  { key: 'week_winner_bonus', label: 'Vencedor da semana', desc: 'Bônus de saldo para quem fecha a semana na frente', format: (v) => `+${v}` },
];

const perWorkoutPct = (goal) => Math.round(100 / goal);

// ---- Goals ----

function goalNote({ me, board, goalChanged }) {
  const nextMonday = addDays(parseDate(board.week_start), 7);
  if (goalChanged) {
    const nextRange = weekRange(toIso(nextMonday), toIso(addDays(nextMonday, 6)));
    return `A mudança vale a partir da semana de ${nextRange}, para não mexer no placar desta semana.`;
  }
  if (me.next_weekly_goal) {
    return `Esta semana segue com ${me.weekly_goal}. A partir de ${dayMonth(nextMonday)}, sua meta passa a ${me.next_weekly_goal} treinos.`;
  }
  const mine = board.players.find((p) => p.is_me);
  return `Nesta semana: ${mine.done} de ${mine.goal}. Cada treino vale ${perWorkoutPct(mine.goal)}% do seu placar.`;
}

function myGoalCard(state) {
  const { me, goalDraft: draft, goalChanged: changed } = state;
  return html`
    <section class="goal-card goal-card--mine">
      <div class="goal-card__label">${avatar({ name: me.first_name, color: me.color, size: 28 })}<span>SUA META SEMANAL</span></div>
      <div class="goal-stepper">
        <button class="goal-stepper__btn" type="button" data-action="goal-dec" aria-label="Diminuir meta" ${draft <= MIN_GOAL ? html`disabled` : ''}>${icon('minus', 20, { stroke: 2.6 })}</button>
        <div class="goal-stepper__value">
          <span class="goal-number${changed ? ' is-changed' : ''}">${draft}</span>
          <span class="goal-unit">treinos<br>por semana</span>
        </div>
        <button class="goal-stepper__btn" type="button" data-action="goal-inc" aria-label="Aumentar meta" ${draft >= MAX_GOAL ? html`disabled` : ''}>${icon('plus', 20, { stroke: 2.6 })}</button>
      </div>
      <p class="goal-card__note">${goalNote(state)}</p>
      ${changed && html`
        <div class="goal-card__actions">
          <button class="btn btn--secondary btn--sm" type="button" data-action="goal-reset">Cancelar</button>
          <button class="btn btn--primary btn--sm" type="button" data-action="goal-save">Salvar meta</button>
        </div>`}
    </section>`;
}

function opponentGoalCard(opponent) {
  if (!opponent) {
    return html`
      <section class="goal-card">
        <div class="goal-card__label"><span>META DA SUA DUPLA</span></div>
        <p class="goal-card__note">Sua dupla ainda não se cadastrou. A meta dela aparece aqui depois do cadastro.</p>
      </section>`;
  }
  return html`
    <section class="goal-card">
      <div class="goal-card__label">${avatar({ name: opponent.name, color: opponent.color, size: 28 })}<span>META DE ${opponent.name.toUpperCase()}</span></div>
      <div class="goal-readonly"><span class="goal-number">${opponent.goal}</span><span class="goal-unit">treinos<br>por semana</span></div>
      <p class="goal-card__note">Cada treino vale ${perWorkoutPct(opponent.goal)}% do placar de ${opponent.name}. Só ${opponent.name} muda a própria meta.</p>
    </section>`;
}

// ---- Streaks ----

function weekCell(week) {
  const label = week.is_current ? 'Esta' : dayMonth(parseDate(week.week_start), { short: true });
  const state = week.goal === null ? 'none' : week.met ? 'met' : 'missed';
  return html`
    <div class="streak-week streak-week--${state}${week.is_current ? ' is-current' : ''}">
      <div class="streak-week__cell" title="${week.goal === null ? 'Antes do cadastro' : `${week.done} de ${week.goal}`}">
        ${week.is_current && !week.met && week.goal ? `${week.done}/${week.goal}` : ''}
      </div>
      <span class="streak-week__label">${label}</span>
    </div>`;
}

function streakRow(player) {
  const next = player.next_badge;
  return html`
    <div class="streak-row player--${player.color}">
      <div class="streak-row__who">
        ${avatar({ name: player.name, color: player.color, size: 48 })}
        <div class="streak-row__numbers">
          <span class="streak-row__name">${player.name}</span>
          <span class="streak-row__streak">${icon('fire', 22)}<span class="display">${player.streak}</span> ${plural(player.streak, 'semana', 'semanas')}</span>
          <span class="streak-row__record">Recorde: ${player.record} ${plural(player.record, 'semana', 'semanas')}</span>
        </div>
      </div>
      <div class="streak-row__detail">
        <div class="streak-weeks">${player.weeks.map(weekCell)}</div>
        <div class="streak-badges">
          ${player.badges.map((badge) => html`
            <span class="streak-badge${badge.earned ? ' is-earned' : ''}" title="${badge.earned ? 'Conquistado' : 'Ainda não conquistado'}">
              ${icon('fire', 14)}${badge.milestone} sem · +${badge.bonus}
            </span>`)}
          <span class="streak-badges__next">${next
            ? `Próximo selo em ${next.weeks_left} ${plural(next.weeks_left, 'semana', 'semanas')}`
            : 'Todos os selos conquistados'}</span>
        </div>
      </div>
    </div>`;
}

const streaksCard = (streaks) => html`
  <section class="panel-card streaks-card">
    <div class="panel-card__head">
      <h2>Sequências</h2>
      <p>Semanas seguidas com a meta batida. Semana perdida zera a sequência, mas não tira pontos.</p>
    </div>
    ${streaks.players.map(streakRow)}
  </section>`;

// ---- Rules ----

function rulesStatus({ rules, opponentName, rulesDirty: dirty }) {
  if (rules.pending?.proposed_by_me) return { text: `Aguardando ${opponentName}`, tone: 'accent' };
  if (rules.pending) return { text: `${rules.pending.proposed_by_name} propôs mudanças`, tone: 'accent' };
  if (dirty) return { text: 'Rascunho', tone: 'strong' };
  return { text: 'Em vigor · aprovadas pelos dois', tone: 'muted' };
}

function ruleRow(def, { rules, rulesDraft: draft, rulesLocked: locked }) {
  const changed = draft[def.key] !== rules.current[def.key];
  return html`
    <div class="rule-row">
      <div class="rule-row__text">
        <div class="rule-row__label">${def.label}${changed && html`<span class="tag-changed">ALTERADO</span>`}</div>
        <div class="rule-row__desc">${def.desc}</div>
      </div>
      <div class="segmented segmented--dark rule-row__options" role="group" aria-label="${def.label}">
        ${rules.options[def.key].map((value) => html`
          <button class="segmented__btn${draft[def.key] === value ? ' is-on' : ''}" type="button" data-rule="${def.key}"
            data-value="${value}" aria-pressed="${draft[def.key] === value}" ${locked ? html`disabled` : ''}>${def.format(value)}</button>`)}
      </div>
    </div>`;
}

function rulesActions({ rules, opponentName, rulesDirty: dirty, hasOpponent }) {
  if (!hasOpponent) {
    return html`<p class="rules-panel__note">As regras só podem mudar quando sua dupla estiver cadastrada.</p>`;
  }
  if (rules.pending?.proposed_by_me) {
    return html`
      <div class="rules-panel__actions">
        <span class="rules-panel__message">Proposta enviada. As regras atuais seguem valendo até ${opponentName} aprovar.</span>
        <button class="btn btn--ghost btn--sm" type="button" data-action="rules-cancel">Cancelar proposta</button>
      </div>`;
  }
  if (rules.pending) {
    return html`
      <div class="rules-panel__actions">
        <span class="rules-panel__message">${rules.pending.proposed_by_name} propôs estas mudanças. As regras atuais seguem valendo até você aprovar.</span>
        <button class="btn btn--secondary btn--sm" type="button" data-action="rules-reject">Recusar</button>
        <button class="btn btn--primary btn--sm" type="button" data-action="rules-approve">Aprovar mudanças</button>
      </div>`;
  }
  if (dirty) {
    return html`
      <div class="rules-panel__actions">
        <button class="btn btn--secondary btn--sm" type="button" data-action="rules-discard">Descartar</button>
        <button class="btn btn--primary btn--sm" type="button" data-action="rules-propose">Propor mudança a ${opponentName}</button>
      </div>`;
  }
  return '';
}

function rulesCard(state) {
  const status = rulesStatus(state);
  return html`
    <section class="panel-card rules-panel">
      <div class="rules-panel__head">
        <div>
          <h2>Regras de pontos</h2>
          <p>Valem para os dois e só mudam quando os dois aprovam. Ao aprovar, os pontos da semana são recalculados.</p>
        </div>
        <span class="status-chip status-chip--${status.tone}">${status.text}</span>
      </div>
      <div class="rules-panel__rows">${RULE_DEFS.map((def) => ruleRow(def, state))}</div>
      <div class="rules-panel__example">
        <span>Exemplo: musculação, 45 min, moderada, com foto</span>
        <span class="rules-panel__example-pts">${calcPoints(45, 'Moderada', true, state.rulesDraft)} pts</span>
      </div>
      ${rulesActions(state)}
    </section>`;
}

export function goalsView(state) {
  return html`
    <div class="goals">
      ${pageHead({ kicker: 'Constância vale mais que volume', title: 'Metas e regras' })}
      <div class="goals__cards">
        ${myGoalCard(state)}
        ${opponentGoalCard(state.board.players.find((p) => !p.is_me))}
      </div>
      ${streaksCard(state.streaks)}
      ${rulesCard(state)}
    </div>`;
}
