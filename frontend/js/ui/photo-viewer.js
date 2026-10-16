// Enlarged proof photo with the workout data; on the duo's workouts, "Mandar parabéns".
// Any element with data-photo='{"id":..}' (the 48px thumbnails) opens it.
import { api, ApiError } from '../core/api.js';
import { cachedScoreboard } from '../core/app-state.js';
import { html } from '../core/dom.js';
import { icon } from '../core/icons.js';
import { session } from '../core/session.js';
import { dayLabel } from '../domain/format.js';
import { avatar } from './avatar.js';
import { openSheet } from './sheet.js';
import { showToast } from './toast.js';

/** Thumbnail button for a workout row (48px). */
export const photoThumb = (workout) => html`
  <button class="photo-thumb" type="button" aria-label="Ver foto do treino"
    data-photo="${JSON.stringify({ id: workout.id, user_id: workout.user_id, user_name: workout.user_name, color: workout.color,
      type: workout.type, duration_min: workout.duration_min, intensity: workout.intensity, date: workout.date, photo_url: workout.photo_url })}">
    <img src="${workout.photo_url}" alt="" loading="lazy">
  </button>`;

function viewerView(workout) {
  const today = cachedScoreboard()?.today || workout.date;
  const fromDuo = workout.user_id !== session.user?.id;
  return html`
    <div class="photo-viewer">
      <div class="photo-viewer__image"><img src="${workout.photo_url}" alt="Foto do treino de ${workout.user_name}"></div>
      <div class="photo-viewer__info">
        ${avatar({ name: workout.user_name, color: workout.color, size: 40 })}
        <div class="photo-viewer__text">
          <div class="photo-viewer__title">${workout.type} · ${workout.duration_min} min · ${workout.intensity}</div>
          <div class="photo-viewer__sub">${workout.user_name} · ${dayLabel(workout.date, today, { long: true })} · treino verificado</div>
        </div>
        <div class="photo-viewer__actions">
          ${fromDuo && html`<button class="btn btn--primary btn--sm" type="button" data-action="cheer">${icon('trophy', 16)}Mandar parabéns</button>`}
          <button class="btn btn--secondary btn--sm" type="button" data-action="close-sheet">Fechar</button>
        </div>
      </div>
    </div>`;
}

export function openPhotoViewer(workout) {
  const sheet = openSheet(viewerView(workout), {
    label: `Foto do treino de ${workout.user_name}`,
    size: 'md',
    onAction: async (action) => {
      if (action !== 'cheer') return;
      try {
        await api.cheer(workout.id);
        sheet.close();
        showToast(`Parabéns enviado para ${workout.user_name}.`);
      } catch (error) {
        if (error instanceof ApiError) showToast(error.message);
      }
    },
  });
}

export function initPhotoViewer() {
  document.addEventListener('click', (event) => {
    const thumb = event.target.closest('[data-photo]');
    if (thumb) openPhotoViewer(JSON.parse(thumb.dataset.photo));
  });
}
