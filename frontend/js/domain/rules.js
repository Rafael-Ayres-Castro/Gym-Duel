// Game constants and the points formula, mirrored from backend/app/scoring.py.
// The backend is the source of truth; this copy only powers the live preview in the check-in.

export const WORKOUT_TYPES = ['Musculação', 'Corrida', 'Funcional', 'Aula', 'Outro'];
export const INTENSITIES = [
  { value: 'Leve', sub: '−5 pts' },
  { value: 'Moderada', sub: 'base' },
  { value: 'Alta', sub: '+5 pts' },
];
export const DURATION_PRESETS = [30, 45, 60, 90];
export const MIN_DURATION = 5;
export const MAX_DURATION = 300;
export const NOTE_MAX = 140;
export const GOAL_OPTIONS = [1, 2, 3, 4, 5, 6, 7];

const INTENSITY_ADJUSTMENT = { Leve: -5, Moderada: 0, Alta: 5 };
const MIN_POINTS = 5;

/** max(5, round(minutes / 3) + intensity adjustment). */
export function calcPoints(minutes, intensity) {
  return Math.max(MIN_POINTS, Math.round(minutes / 3) + INTENSITY_ADJUSTMENT[intensity]);
}

export const isValidDuration = (minutes) => Number.isInteger(minutes) && minutes >= MIN_DURATION && minutes <= MAX_DURATION;
