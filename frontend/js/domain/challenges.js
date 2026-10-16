// Labels of challenges (pt-BR, from the v2 prototype). The backend decides progress and winners;
// these helpers only describe them. challengeTitle mirrors backend/app/texts.py for the live preview.
import { addDays, parseDate, plural, toIso, weekRange } from './format.js';

export const CHALLENGE_KINDS = [
  { value: 'count', label: 'Mais treinos' },
  { value: 'minutes', label: 'Mais minutos' },
  { value: 'goal', label: 'Primeiro a bater a meta' },
];
export const CHALLENGE_TYPES = ['Musculação', 'Corrida', 'Funcional', 'Aula'];
export const CHALLENGE_STAKES = [10, 20, 50];

const MONTHS = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];

export function challengeTitle(kind, workoutType, period) {
  const sport = workoutType ? workoutType.toLowerCase() : null;
  let base;
  if (kind === 'count') base = `Mais treinos${sport ? ` de ${sport}` : ''}`;
  else if (kind === 'minutes') base = `Mais minutos${sport ? ` de ${sport}` : ' de treino'}`;
  else base = 'Primeiro a bater a meta';
  return base + ({ week: ' na semana', weekend: ' no fim de semana' }[period] || '');
}

/** Monday–Sunday or Saturday–Sunday of the current week, as ISO dates. */
export function periodDates(period, todayIso) {
  const today = parseDate(todayIso);
  const monday = addDays(today, -((today.getUTCDay() + 6) % 7));
  const sunday = addDays(monday, 6);
  return period === 'weekend'
    ? { starts: toIso(addDays(sunday, -1)), ends: toIso(sunday) }
    : { starts: toIso(monday), ends: toIso(sunday) };
}

/** "12 a 18 de out" or "Sáb e dom, 17 e 18 de out". */
export function periodLabel(period, startsIso, endsIso) {
  if (period !== 'weekend') return weekRange(startsIso, endsIso);
  const sat = parseDate(startsIso);
  const sun = parseDate(endsIso);
  if (sat.getUTCMonth() === sun.getUTCMonth()) return `Sáb e dom, ${sat.getUTCDate()} e ${sun.getUTCDate()} de ${MONTHS[sun.getUTCMonth()]}`;
  return `Sáb e dom, ${sat.getUTCDate()} de ${MONTHS[sat.getUTCMonth()]} e ${sun.getUTCDate()} de ${MONTHS[sun.getUTCMonth()]}`;
}

/** Chip with the deadline: "Até dom, 18" or "Sáb e dom". */
export const endsLabel = (period, endsIso) => (period === 'weekend' ? 'Sáb e dom' : `Até dom, ${parseDate(endsIso).getUTCDate()}`);

export const stakeLabel = (points, text) => (points ? `Vale +${points} pts para quem vencer` : `Vale: ${text || 'descreva o combinado'}`);

export function valueLabel(kind, value) {
  if (kind === 'count') return `${value} ${plural(value, 'treino', 'treinos')}`;
  if (kind === 'minutes') return `${value} min`;
  return `${value}%`;
}

/** Bar width: % of the goal, or the share of the larger value. */
export function barWidth(kind, value, values) {
  if (kind === 'goal') return Math.min(100, value);
  return Math.round((value / Math.max(1, ...values)) * 100);
}

/** "Você na frente", "Ana na frente", "Empatado", "Ninguém pontuou ainda", "Ana bateu primeiro". */
export function statusOf(challenge) {
  const [me, duo] = challenge.players;
  const nameOf = (id) => (id === me.user_id ? 'Você' : duo.name);
  if (challenge.first_to_goal_id) return { text: `${nameOf(challenge.first_to_goal_id)} bateu primeiro`, who: challenge.first_to_goal_id === me.user_id ? 'me' : 'duo' };
  if (!challenge.leader_id) return { text: me.value === 0 && duo.value === 0 ? 'Ninguém pontuou ainda' : 'Empatado', who: null };
  return challenge.leader_id === me.user_id ? { text: 'Você na frente', who: 'me' } : { text: `${duo.name} na frente`, who: 'duo' };
}

/** Result of a finished challenge: "Você venceu · +20 pts" or "Sem vencedor". */
export function resultLabel(challenge, myId) {
  if (!challenge.winner_id) return 'Sem vencedor';
  const who = challenge.winner_id === myId ? 'Você venceu' : `${challenge.winner_name} venceu`;
  return challenge.stake_points ? `${who} · +${challenge.stake_points} pts` : who;
}
