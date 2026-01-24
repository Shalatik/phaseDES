# mev_sim/utils/logging.py
import logging
from pathlib import Path

def setup_logging(log_file="output_log.txt", level=logging.INFO):
    log_path = Path(log_file)

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_path, mode="w"),
            logging.StreamHandler(),
        ],
    )
