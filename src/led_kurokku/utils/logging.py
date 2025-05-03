from datetime import datetime
import logging
import sys
import traceback


class LoguruLikeFormatter(logging.Formatter):
    """A formatter that mimics loguru's default output style"""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[41m",  # Red background
        "RESET": "\033[0m",  # Reset color
    }

    def format(self, record):
        # Get the log level name and apply color
        levelname = record.levelname
        color = self.COLORS.get(levelname, self.COLORS["RESET"])
        colored_levelname = f"{color}{levelname:<8}{self.COLORS['RESET']}"

        # Format the timestamp like loguru does
        timestamp = datetime.fromtimestamp(record.created).strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )[:-3]

        # Get the module and line info
        module = record.module
        lineno = record.lineno

        # Format the message part
        log_message = super().format(record)

        # Format the full message in loguru style
        formatted_message = (
            f"{timestamp} | {colored_levelname} | {module}:{lineno} - {log_message}"
        )

        # Add traceback for errors if available
        if record.exc_info:
            # Format exception info
            exc_text = "".join(traceback.format_exception(*record.exc_info))
            formatted_message += f"\n{exc_text}"

        return formatted_message


def setup_logging(level=logging.INFO, filename=None):
    """Configure standard logging to look like loguru"""
    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    formatter = LoguruLikeFormatter()

    # Create a console handler
    if not filename:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    else:
        file_handler = logging.FileHandler(filename)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    return root_logger
