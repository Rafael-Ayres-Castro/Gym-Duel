// pt-BR labels used across screens. Texts follow the prototype (design/Gym Duel Web.dc.html).
// Dates arrive from the API as "YYYY-MM-DD" (São Paulo calendar days) and are handled as plain
// calendar dates in UTC, so the browser's own timezone never shifts a day.

const DOW_SHORT = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'];
const DOW_FULL = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo'];
const MONTHS_SHORT = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];
const MONTHS_FULL = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'];
export const DAY_INITIALS = ['S', 'T', 'Q', 'Q', 'S', 'S', 'D'];

export const plural = (count, singular, pluralForm) => (count === 1 ? singular : pluralForm);
export const firstName = (name) => (name || '').trim().split(/\s+/)[0] || name;
export const initial = (name) => (firstName(name)[0] || '?').toUpperCase();

// ---- Calendar dates ----

export function parseDate(iso) {
  const [y, m, d] = iso.split('-').map(Number);
  return new Date(Date.UTC(y, m - 1, d));
}
export const toIso = (date) => date.toISOString().slice(0, 10);
export const addDays = (date, days) => new Date(date.getTime() + days * 86400000);
/** 0 = Monday … 6 = Sunday (the app's week starts on Monday). */
export const weekdayIndex = (date) => (date.getUTCDay() + 6) % 7;
const sameDay = (a, b) => a.getTime() === b.getTime();

/** "qui, 16 out" */
export function shortDate(date) {
  return `${DOW_SHORT[weekdayIndex(date)].toLowerCase()}, ${date.getUTCDate()} ${MONTHS_SHORT[date.getUTCMonth()]}`;
}

/**
 * "Hoje" / "Ontem" / "Ter, 14 out". With `long`, today and yesterday also carry the date:
 * "Hoje · qui, 16 out" (used as history group titles).
 */
export function dayLabel(dateIso, todayIso, { long = false } = {}) {
  const date = parseDate(dateIso);
  const today = parseDate(todayIso);
  if (sameDay(date, today)) return long ? `Hoje · ${shortDate(date)}` : 'Hoje';
  if (sameDay(date, addDays(today, -1))) return long ? `Ontem · ${shortDate(date)}` : 'Ontem';
  return `${DOW_SHORT[weekdayIndex(date)]}, ${date.getUTCDate()} ${MONTHS_SHORT[date.getUTCMonth()]}`;
}

/** "13 a 19 de out" or, across months, "29 de set a 5 de out". */
export function weekRange(startIso, endIso) {
  const start = parseDate(startIso);
  const end = parseDate(endIso);
  const endText = `${end.getUTCDate()} de ${MONTHS_SHORT[end.getUTCMonth()]}`;
  if (start.getUTCMonth() === end.getUTCMonth()) return `${start.getUTCDate()} a ${endText}`;
  return `${start.getUTCDate()} de ${MONTHS_SHORT[start.getUTCMonth()]} a ${endText}`;
}

/** "20 de out", or "20 out" with { short: true } (labels of the streak grid). */
export function dayMonth(date, { short = false } = {}) {
  const month = MONTHS_SHORT[date.getUTCMonth()];
  return short ? `${date.getUTCDate()} ${month}` : `${date.getUTCDate()} de ${month}`;
}

/** "Outubro até agora" */
export const monthSoFar = (todayIso) => `${MONTHS_FULL[parseDate(todayIso).getUTCMonth()]} até agora`;

// ---- Scoreboard texts ----

/** Days left in the week: { weekday: "Quinta-feira", left: "3 dias pela frente" }. */
export function daysLeft(todayIso, weekEndIso) {
  const today = parseDate(todayIso);
  const left = Math.round((parseDate(weekEndIso) - today) / 86400000);
  let text;
  if (left === 0) text = 'último dia';
  else text = `${left} ${plural(left, 'dia restante', 'dias pela frente')}`;
  return { weekday: DOW_FULL[weekdayIndex(today)], left: text };
}

/** Message under the desktop "Dias de treino" grid. */
export function daysMessage(todayIso, me) {
  const missing = me.goal - me.done;
  if (missing <= 0) return 'Sua meta da semana está batida. Treinos extras somam pontos para o desempate.';
  const weekday = DOW_FULL[weekdayIndex(parseDate(todayIso))].toLowerCase();
  return `Hoje é ${weekday}. ${plural(missing, 'Falta', 'Faltam')} ${missing} ${plural(missing, 'treino', 'treinos')} até domingo para fechar sua meta.`;
}

/** "Boa semana" while nobody trained yet; otherwise by time of day (the prototype was set in the morning). */
export function greeting(name, weekIsEmpty, now = new Date()) {
  if (weekIsEmpty) return `Boa semana, ${name}`;
  const hour = now.getHours();
  const salute = hour >= 5 && hour < 12 ? 'Bom dia' : hour >= 12 && hour < 18 ? 'Boa tarde' : 'Boa noite';
  return `${salute}, ${name}`;
}

export const streakShort = (weeks) => `${weeks} sem`;
export const streakLong = (weeks) => `${weeks} ${plural(weeks, 'semana', 'semanas')}`;
export const pointsLabel = (points) => `${points} pts`;
export const workoutsLabel = (count) => plural(count, 'treino', 'treinos');
