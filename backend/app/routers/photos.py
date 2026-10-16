"""Serves locally stored photos through signed, expiring URLs (S3 storage serves its own)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse

from ..errors import api_error
from ..storage import LocalStorage, PhotoStorage, get_storage

router = APIRouter(tags=["photos"])


@router.get("/photos/{key:path}", include_in_schema=False)
def read_photo(
    key: str,
    exp: int = Query(...),
    sig: str = Query(...),
    storage: PhotoStorage = Depends(get_storage),
):
    path = storage.read_signed(key, exp, sig) if isinstance(storage, LocalStorage) else None
    if path is None:
        raise api_error(404, "not_found", "Foto não encontrada ou link expirado.")
    # Private, short-lived: browsers may cache it only for the life of the signed URL.
    return FileResponse(path, media_type="image/jpeg", headers={"Cache-Control": "private, max-age=600"})
