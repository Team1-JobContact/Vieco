"""Expose website assets without exposing development files or request logs."""
from pathlib import PurePosixPath

from starlette.exceptions import HTTPException
from starlette.staticfiles import StaticFiles


class FrontendFiles(StaticFiles):
    async def get_response(self, path, scope):
        parts = PurePosixPath(path.replace("\\", "/")).parts
        if any(part.startswith(".") for part in parts):
            raise HTTPException(status_code=404)
        if path not in ("", ".", "index.html") and (not parts or parts[0] not in ("pages", "src")):
            raise HTTPException(status_code=404)
        return await super().get_response(path, scope)
