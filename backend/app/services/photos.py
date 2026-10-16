"""Proof photos: validation, re-encoding without metadata, storage and the "parabéns" cheer.

Re-encoding with Pillow drops every EXIF field (GPS location included), applies the
camera orientation first so the picture does not end up sideways, and caps the size.
"""

from __future__ import annotations

import datetime as dt
import io
import uuid

from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy.orm import Session

from ..errors import api_error
from ..models import User, Workout
from ..storage import PhotoStorage
from . import notifications, players, rules
from .workouts import checkin_result, own_recent_workout

MAX_UPLOAD_BYTES = 8 * 1024 * 1024
MAX_SIDE_PX = 1600
JPEG_QUALITY = 82

Image.MAX_IMAGE_PIXELS = 50_000_000  # refuse decompression bombs


def clean_image(data: bytes) -> bytes:
    """JPEG with the longest side ≤ 1600 px and no metadata. Raises 413/422 for bad uploads."""
    if len(data) > MAX_UPLOAD_BYTES:
        raise api_error(413, "photo_too_big", "A foto pode ter no máximo 8 MB.")
    try:
        with Image.open(io.BytesIO(data)) as image:
            image = ImageOps.exif_transpose(image)
            image.thumbnail((MAX_SIDE_PX, MAX_SIDE_PX))
            output = io.BytesIO()
            # No exif= argument: the new file carries no metadata at all.
            image.convert("RGB").save(output, "JPEG", quality=JPEG_QUALITY, optimize=True)
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise api_error(422, "invalid_photo", "Esse arquivo não parece ser uma foto. Tente outra imagem.") from None
    return output.getvalue()


def attach_photo(
    db: Session, user: User, workout_id: int, data: bytes, today: dt.date, storage: PhotoStorage
) -> dict:
    """Store the photo, apply the photo bonus and return the updated check-in result."""
    workout = own_recent_workout(db, user, workout_id, today, "mudar a foto de")
    image = clean_image(data)
    key = f"workouts/{workout.id}-{uuid.uuid4().hex}.jpg"
    try:
        storage.save(key, image)
    except Exception:  # storage down: the workout stays saved without the photo
        raise api_error(503, "storage_unavailable", "Não deu para guardar a foto agora. Tente de novo.") from None

    old_key, workout.photo_key = workout.photo_key, key
    workout.points = rules.workout_points(workout, rules.rules_for_date(db, workout.date))
    db.commit()
    if old_key:
        storage.delete(old_key)
    return checkin_result(db, user, workout, today, storage)


def cheer(db: Session, user: User, workout_id: int) -> None:
    """Congratulate the other member for a workout: a notification for them."""
    workout = db.get(Workout, workout_id)
    if workout is None:
        raise api_error(404, "not_found", "Treino não encontrado.")
    if workout.user_id == user.id:
        raise api_error(403, "own_workout", "Os parabéns são para os treinos da sua dupla.")
    notifications.notify(
        db, workout.user_id, "cheer",
        f"{players.display_name(user)} mandou parabéns pelo seu treino de {workout.type.lower()}!",
        {"workout_id": workout.id},
    )
    db.commit()
