"""Налаштування логування (рівні INFO / WARNING / ERROR)."""

import logging


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)-7s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )
    # SQL-запити не виводимо, щоб у логах не з'являлися чутливі дані
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
