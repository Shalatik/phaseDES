# mev_sim/utils/logging.py
import logging
from pathlib import Path

def setup_logging(log_file="output_log.txt", level=logging.INFO):
    log_path = Path(log_file)

    formatter = logging.Formatter(
        fmt="%(message)s"   # <-- jen samotná zpráva
    )

    file_handler = logging.FileHandler(log_path, mode="w")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    logging.root.handlers.clear()
    logging.root.setLevel(level)
    logging.root.addHandler(file_handler)