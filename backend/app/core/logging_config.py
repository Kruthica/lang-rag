"""
Centralized logging with optional ANSI colors on supported terminals.

Production tip: switch to structured JSON logs behind an env flag if you ship
to a log aggregator; colorama is great for local/dev readability.
"""

import logging
import sys
from typing import Optional

try:
    from colorama import Fore, Style, init as colorama_init

    colorama_init(autoreset=True)
    _COLORAMA = True
except ImportError:
    _COLORAMA = False
    Fore = Style = None  # type: ignore


class ColorFormatter(logging.Formatter):
    """Prefix log levels with colors when colorama is available."""

    LEVEL_COLORS = {
        logging.DEBUG: Fore.CYAN if _COLORAMA else "",
        logging.INFO: Fore.GREEN if _COLORAMA else "",
        logging.WARNING: Fore.YELLOW if _COLORAMA else "",
        logging.ERROR: Fore.RED if _COLORAMA else "",
        logging.CRITICAL: Fore.MAGENTA if _COLORAMA else "",
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.LEVEL_COLORS.get(record.levelno, "")
        reset = Style.RESET_ALL if _COLORAMA else ""
        record.levelname = f"{color}{record.levelname}{reset}"
        return super().format(record)


def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logger once at application startup."""
    handler = logging.StreamHandler(sys.stdout)
    fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    if _COLORAMA:
        handler.setFormatter(ColorFormatter(fmt))
    else:
        handler.setFormatter(logging.Formatter(fmt))

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)
    root.addHandler(handler)

    # Reduce noisy third-party loggers
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Convenience accessor for module-level loggers."""
    return logging.getLogger(name or "rag")
