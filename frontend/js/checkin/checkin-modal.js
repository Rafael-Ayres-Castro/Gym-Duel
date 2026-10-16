// Check-in flow: full screen on mobile, modal on desktop. Opens on EVENTS.openCheckin,
// pre-filled with the user's last workout; Enter saves, Esc closes.
import { api, ApiError } from '../core/api.js';
import { loadScoreboard, setScoreboard } from '../core/app-state.js';
import { createElement, html, on, renderInto } from '../core/dom.js';
import { emit, EVENTS, listen } from '../core/events.js';
import { PhotoError, preparePhoto } from '../core/image.js';
import { isDesktop } from '../core/media.js';
import { go } from '../core/router.js';
import { addDays, parseDate, toIso } from '../domain/format.js';
import { calcPoints, DURATION_PRESETS, isValidDuration } from '../domain/rules.js';
import { showToast } from '../ui/toast.js';
import { checkinFormView } from './checkin-form.js';
import { successView } from './success-view.js';

const DEFAULT_FORM = { type: 'Musculação', duration: 45, custom: '', intensity: 'Moderada', day: 'today', note: '' };

let modal = null; // state of the open check-in, null when closed

/** Same pre-fill rule as the prototype: last workout's choices, odd durations go to "outro tempo". */
function prefill(lastWorkout) {
  if (!lastWorkout) return { ...DEFAULT_FORM };
  const isPreset = DURATION_PRESETS.includes(lastWorkout.duration_min);
  return {
    ...DEFAULT_FORM,
    type: lastWorkout.type,
    intensity: lastWorkout.intensity,
    duration: isPreset ? lastWorkout.duration_min : DEFAULT_FORM.duration,
    custom: isPreset ? '' : String(lastWorkout.duration_min),
  };
}

/** Minutes chosen, or null while "outro tempo" holds an invalid value. */
function chosenDuration(form) {
  if (form.custom === '') return form.duration;
  const minutes = Number(form.custom);
  return isValidDuration(minutes) ? minutes : null;
}

const isSelected = (form, key, value) => (key === 'duration' ? form.custom === '' && Number(value) === form.duration : form[key] === value);

/** Reflect the form state on the screen without re-rendering (keeps focus in the inputs). */
function sync() {
  const { dialog, form } = modal;
  const minutes = chosenDuration(form);
  dialog.querySelectorAll('[data-set]').forEach((option) => {
    const selected = isSelected(form, option.dataset.set, option.dataset.value);
    option.classList.toggle('is-on', selected);
    option.setAttribute('aria-pressed', String(selected));
  });
  const custom = dialog.querySelector('.checkin__custom');
  custom.classList.toggle('is-valid', form.custom !== '' && minutes !== null);
  custom.classList.toggle('is-invalid', form.custom !== '' && minutes === null);
  dialog.querySelector('.checkin__dur-error').hidden = !(form.custom !== '' && minutes === null);
  const hasPhoto = Boolean(modal.photo);
  dialog.querySelector('[data-bind="points"]').textContent = minutes ? `+${calcPoints(minutes, form.intensity, hasPhoto, modal.rules)}` : '—';
  dialog.querySelector('[data-bind="summary"]').textContent =
    `${form.type} · ${minutes ? `${minutes} min` : '— min'} · ${form.intensity}${hasPhoto ? ' · com foto' : ''}`;
  dialog.querySelector('.photo-pick').dataset.photoState = hasPhoto ? 'filled' : 'empty';
  dialog.querySelector('[data-action="save"]').disabled = !minutes || modal.saving || modal.preparingPhoto;
}

function showPhotoError(message) {
  const error = modal.dialog.querySelector('.photo-pick__error');
  error.hidden = !message;
  error.querySelector('span').textContent = message || '';
}

/** Resize the chosen picture right away, so saving is instant and errors show before saving. */
async function choosePhoto(input) {
  const file = input.files?.[0];
  input.value = ''; // allow choosing the same file again after "Remover"
  if (!file) return;
  showPhotoError(null);
  modal.preparingPhoto = true;
  sync();
  try {
    const blob = await preparePhoto(file);
    if (!modal) return;
    setPhoto({ blob, url: URL.createObjectURL(blob) });
  } catch (error) {
    if (!(error instanceof PhotoError)) throw error;
    showPhotoError(error.message);
  } finally {
    if (modal) {
      modal.preparingPhoto = false;
      sync();
    }
  }
}

function setPhoto(photo) {
  if (modal.photo) URL.revokeObjectURL(modal.photo.url);
  modal.photo = photo;
  const thumb = modal.dialog.querySelector('.photo-pick__thumb');
  if (photo) thumb.src = photo.url;
  else thumb.removeAttribute('src');
  sync();
}

/** Upload after the workout exists. On failure the workout stays saved, without the bonus. */
async function uploadPhoto(result) {
  try {
    return await api.uploadPhoto(result.workout.id, modal.photo.blob);
  } catch (error) {
    if (!(error instanceof ApiError)) throw error;
    return { ...result, photoError: error.message };
  }
}

function showError(message) {
  const error = modal.dialog.querySelector('.checkin__error');
  error.hidden = !message;
  error.querySelector('span').textContent = message || '';
}

async function save() {
  const { form, today } = modal;
  const minutes = chosenDuration(form);
  if (!minutes || modal.saving) return;

  const button = modal.dialog.querySelector('[data-action="save"]');
  modal.saving = true;
  button.textContent = 'Salvando…';
  showError(null);
  sync();
  try {
    const result = await api.checkin({
      type: form.type,
      duration_min: minutes,
      intensity: form.intensity,
      date: form.day === 'today' ? today : toIso(addDays(parseDate(today), -1)),
      note: form.note.trim(),
    });
    const final = modal.photo ? await uploadPhoto(result) : result;
    setScoreboard(final.scoreboard);
    showSuccess(final);
    emit(EVENTS.workoutSaved, final);
  } catch (error) {
    if (!(error instanceof ApiError)) throw error;
    modal.saving = false;
    button.textContent = 'Salvar check-in';
    showError(error.message);
    sync();
  }
}

function showSuccess(result) {
  modal.result = result;
  modal.dialog.classList.add('checkin--success');
  renderInto(modal.dialog, successView(result, { wide: isDesktop() }));
  modal.dialog.querySelector('[data-action="close"]').focus({ preventScroll: true });
}

async function retryPhoto(button) {
  button.disabled = true;
  button.textContent = 'Enviando…';
  const final = await uploadPhoto(modal.result);
  if (!modal) return;
  if (!final.photoError) {
    setScoreboard(final.scoreboard);
    emit(EVENTS.workoutSaved, final);
  }
  showSuccess(final);
}

function close() {
  if (!modal?.overlay) return;
  const { overlay, cleanup, previousFocus } = modal;
  cleanup.forEach((off) => off());
  if (modal.photo) URL.revokeObjectURL(modal.photo.url);
  overlay.remove();
  document.body.classList.remove('has-modal');
  modal = null;
  previousFocus?.focus?.({ preventScroll: true });
}

function onKeydown(event) {
  if (event.key === 'Escape') {
    event.preventDefault();
    close();
  } else if (event.key === 'Enter' && !event.target.closest('textarea, label, [data-action="close"], [data-action="history"], [data-action="retry-photo"], [data-action="remove-photo"]')) {
    event.preventDefault();
    if (modal.result) close();
    else save();
  }
}

function bindEvents(overlay, dialog) {
  const cleanup = [
    on(dialog, 'click', '[data-set]', (_, option) => {
      const { set: key, value } = option.dataset;
      if (key === 'duration') {
        modal.form.duration = Number(value);
        modal.form.custom = '';
        dialog.querySelector('[name="custom"]').value = '';
      } else {
        modal.form[key] = value;
      }
      sync();
    }),
    on(dialog, 'input', '[name="custom"]', (_, input) => {
      input.value = input.value.replace(/\D/g, '').slice(0, 3);
      modal.form.custom = input.value;
      sync();
    }),
    on(dialog, 'input', '[name="note"]', (_, textarea) => { modal.form.note = textarea.value; }),
    on(dialog, 'change', '[name="photo"], [name="photo-camera"]', (_, input) => choosePhoto(input)),
    on(dialog, 'click', '[data-action]', (_, button) => {
      const { action } = button.dataset;
      if (action === 'save') save();
      if (action === 'close') close();
      if (action === 'history') { close(); go('history'); }
      if (action === 'remove-photo') setPhoto(null);
      if (action === 'retry-photo') retryPhoto(button);
    }),
  ];
  // Click on the dimmed backdrop (desktop) closes, like the prototype.
  const onBackdrop = (event) => { if (event.target === overlay) close(); };
  overlay.addEventListener('click', onBackdrop);
  document.addEventListener('keydown', onKeydown);
  cleanup.push(() => overlay.removeEventListener('click', onBackdrop), () => document.removeEventListener('keydown', onKeydown));
  return cleanup;
}

async function open() {
  if (modal) return;
  modal = { opening: true }; // blocks a second open while loading
  let board;
  let lastWorkout;
  try {
    [board, [lastWorkout]] = await Promise.all([
      loadScoreboard(), // fresh: rules may have changed since the screen loaded
      api.workouts({ person: 'me', period: 'all', limit: 1 }),
    ]);
  } catch (error) {
    modal = null;
    if (error instanceof ApiError) showToast(error.message);
    return;
  }

  const overlay = createElement(html`
    <div class="checkin-overlay">
      <div class="checkin" role="dialog" aria-modal="true" aria-labelledby="checkin-title" tabindex="-1">
        ${checkinFormView(board.today, board.rules, board.players.find((p) => !p.is_me)?.name || 'Sua dupla')}
      </div>
    </div>`);
  const dialog = overlay.firstElementChild;
  modal = {
    overlay, dialog, form: prefill(lastWorkout), today: board.today, rules: board.rules,
    photo: null, preparingPhoto: false, saving: false, result: null, previousFocus: document.activeElement,
  };
  dialog.querySelector('[name="custom"]').value = modal.form.custom;
  dialog.querySelector('[name="custom"]').placeholder = isDesktop() ? 'Outro' : '—';
  modal.cleanup = bindEvents(overlay, dialog);

  document.body.append(overlay);
  document.body.classList.add('has-modal');
  sync();
  dialog.focus({ preventScroll: true });
}

export function initCheckin() {
  listen(EVENTS.openCheckin, open);
}
