import logging
from fastapi import FastAPI

logger = logging.getLogger(__name__)


def setup_admin(app: FastAPI) -> None:
    """Подключает fastapi-amis-admin к приложению, если пакет совместим с окружением."""
    try:
        from apps.admin.setup import mount_admin

        mount_admin(app)
    except Exception as exc:
        logger.warning(
            "Admin panel is disabled: fastapi-amis-admin import/mount failed (%s)",
            exc,
        )


__all__ = ["setup_admin"]
