import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.loader import load_data


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("app.log")],
    )


def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Starting Worship Scheduler Application...")

    try:
        members, demands, unavailability = load_data()
        logger.info("Data loaded successfully.")

        # TODO: Initialize and run Solver

    except Exception as e:
        logger.critical(f"Critical Failure: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
