"""Uniform API errors: `{"detail": {"code": ..., "message": ...}}`.

`code` is stable for the frontend to branch on; `message` is ready to show (pt-BR).
"""

from __future__ import annotations

from fastapi import HTTPException


def api_error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})
