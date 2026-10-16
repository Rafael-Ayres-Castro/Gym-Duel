// Game constants and the points formula, mirrored from backend/app/scoring.py.
// The backend is the source of truth; this copy only powers live previews (check-in, rules screen).

export const WORKOUT_TYPES = ['Musculação', 'Corrida', 'Funcional', 'Aula', 'Outro'];
export const INTENSITY_NAMES = ['Leve', 'Moderada', 'Alta'];
export const DURATION_PRESETS = [30, 45, 60, 90];
export const MIN_DURATION = 5;
export const MAX_DURATION = 300;
export const NOTE_MAX = 140;
export const GOAL_OPTIONS = [1, 2, 3, 4, 5, 6, 7];
export const MIN_GOAL = 1;
export const MAX_GOAL = 7;

export const DEFAULT_RULES = { minutes_per_point: 3, intensity_adjust: 5, photo_bonus: 5, week_winner_bonus: 20 };
const INTENSITY_SIGN = { Leve: -1, Moderada: 0, Alta: 1 };
const MIN_POINTS = 5;

/** max(5, round(minutes / minutes_per_point) ± intensity adjustment + photo bonus). */
export function calcPoints(minutes, intensity, hasPhoto = false, rules = DEFAULT_RULES) {
  const base = Math.round(minutes / rules.minutes_per_point) + INTENSITY_SIGN[intensity] * rules.intensity_adjust;
  return Math.max(MIN_POINTS, base + (hasPhoto ? rules.photo_bonus : 0));
}

/** Sub-labels of the intensity options under the given rules: "−5 pts", "base", "+5 pts". */
export function intensityOptions(rules = DEFAULT_RULES) {
  const adjust = rules.intensity_adjust;
  return [
    { value: 'Leve', sub: adjust ? `−${adjust} pts` : 'base' },
    { value: 'Moderada', sub: 'base' },
    { value: 'Alta', sub: adjust ? `+${adjust} pts` : 'base' },
  ];
}

export const isValidDuration = (minutes) => Number.isInteger(minutes) && minutes >= MIN_DURATION && minutes <= MAX_DURATION;
