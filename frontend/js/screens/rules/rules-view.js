// Markup of the "Regras" screen. Numbers come from GET /api/rules, never hard-coded here,
// so the screen always matches the rules the backend applies.
import { html } from '../../core/dom.js';
import { icon } from '../../core/icons.js';
import { plural } from '../../domain/format.js';

const adjustmentLabel = (value) => (value === 0 ? 'base' : `${value > 0 ? '+' : '−'}${Math.abs(value)} pts`);

const card = (title, iconName, body, cls = '') => html`
  <section class="rules-card ${cls}">
    <h2 class="rules-card__title"><span class="rules-card__icon">${icon(iconName, 18)}</span>${title}</h2>
    ${body}
  </section>`;

function pointsCard(rules) {
  return card('Pontos por treino', 'bolt', html`
    <p class="rules-formula"><span class="display">1 pt</span> a cada ${rules.minutes_per_point} minutos de treino</p>
    <div class="rules-intensity">
      ${Object.entries(rules.intensity_adjustment).map(([name, value]) => html`
        <div class="rules-intensity__item"><span>${name}</span><strong>${adjustmentLabel(value)}</strong></div>`)}
    </div>
    <p class="rules-note">Todo treino vale no mínimo ${rules.min_points} pontos.</p>
    <ul class="rules-examples">
      ${rules.examples.map((example) => html`
        <li><span>${example.duration_min} min · ${example.intensity}</span><strong>+${example.points} pts</strong></li>`)}
    </ul>`);
}

function leaderCard(goal) {
  const perWorkout = Math.round(100 / goal);
  return card('Quem lidera a semana', 'crown', html`
    <ol class="rules-steps">
      <li><span><strong>Maior % da meta.</strong> O placar compara a % da meta pessoal de cada um, não o total de pontos.</span></li>
      <li><span><strong>Empatou na %?</strong> Vence quem somou mais pontos na semana.</span></li>
      <li><span><strong>Empate total?</strong> Ninguém lidera, e o próximo treino desempata.</span></li>
    </ol>
    <p class="rules-highlight">
      Sua meta é de ${goal} ${plural(goal, 'treino', 'treinos')} por semana: cada treino vale
      <strong>${perWorkout}%</strong> no seu placar. A % para em 100%, mas treinos extras continuam somando pontos para o desempate.
    </p>`);
}

const streakCard = () => card('Sequência', 'fire', html`
  <p class="rules-text">Conta quantas semanas seguidas você bateu a sua meta. A semana atual entra na conta assim que a meta é batida.</p>
  <p class="rules-text">Fechou uma semana sem bater a meta? A sequência volta a zero.</p>`, 'rules-card--fire');

function checkinCard(rules) {
  const perDay = rules.max_workouts_per_day;
  return card('Check-in', 'check', html`
    <ul class="rules-list">
      <li>Vale para <strong>hoje ou ontem</strong>. Esqueceu de registrar? Ainda dá tempo no dia seguinte.</li>
      <li>${perDay === 1 ? html`<strong>1 treino por dia</strong> conta pontos` : html`Até <strong>${perDay} treinos por dia</strong> contam pontos`}.</li>
      <li>Duração de ${rules.min_duration_min} a ${rules.max_duration_min} minutos.</li>
      <li>A semana vai de <strong>segunda a domingo</strong> (horário de Brasília) e o placar zera toda segunda.</li>
      <li>A meta pode ir de ${rules.min_weekly_goal} a ${rules.max_weekly_goal} treinos. Uma mudança vale da semana atual em diante e não muda semanas passadas.</li>
    </ul>`);
}

const rewardsCard = () => card('Pontos e prêmios', 'trophy', html`
  <p class="rules-text">Em breve, os pontos acumulados vão poder ser trocados por prêmios que vocês combinarem, como escolher o filme ou ganhar um jantar.</p>
  <span class="soon-badge">EM BREVE</span>`);

export function rulesView(rules, user) {
  return html`
    <div class="rules">
      <header class="rules__top">
        <span class="rules__kicker">Como funciona o Gym Duel</span>
        <h1 class="rules__title display">Regras</h1>
      </header>
      <p class="rules__intro">${icon('trophy', 20)}<span>Cada treino vira ponto, mas quem decide a semana é a <strong>% da meta pessoal</strong>. Assim, níveis diferentes de treino têm a mesma chance de ganhar.</span></p>
      <div class="rules__grid">
        ${pointsCard(rules)}
        ${leaderCard(user.weekly_goal)}
        ${checkinCard(rules)}
        ${streakCard()}
        ${rewardsCard()}
      </div>
    </div>`;
}
