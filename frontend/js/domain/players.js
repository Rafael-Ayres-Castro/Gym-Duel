// Presentation state of a player on the scoreboard (leader / trained / no workout yet).
import { plural } from './format.js';

/** @returns {'lead'|'active'|'empty'} */
export function playerState(player) {
  if (player.is_leader) return 'lead';
  return player.done > 0 ? 'active' : 'empty';
}

export const goalCaption = (player) => `${player.done} de ${player.goal} ${plural(player.goal, 'treino', 'treinos')}`;

export const splitPlayers = (board) => ({
  me: board.players.find((p) => p.is_me),
  opponent: board.players.find((p) => !p.is_me) || null,
});

export const weekIsEmpty = (board) => board.players.every((p) => p.done === 0);
