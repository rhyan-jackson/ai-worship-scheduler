import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.config import AppConfig
from src.exporter import export_raw_result, preview_raw
from src.loader import load_data
from src.solver import ServiceSolver


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
        # Initialize centralized config
        config = AppConfig()

        # Load Data
        members, demands, unavailability = load_data(config=config)
        logger.info(
            f"Data loaded successfully. {len(members)} members, {len(demands)} demands."
        )

        # Initialize Solver
        solver = ServiceSolver(members, demands, unavailability)

        # Build Constraints
        logger.info("Building mathematical model...")
        solver.build_model()

        # Solve
        logger.info("Solving... (this might take a moment)")
        raw_solution = solver.solve()

        # Handle Output
        if raw_solution.empty:
            raise Exception(
                "No feasible solution found! Please check constraints or member availability."
            )

        logger.info(f"Optimization Success! Generated {len(raw_solution)} assignments.")

        # Export to CSV the RAW result
        export_raw_result(raw_solution, config=config)
        preview_raw(raw_solution)

    except Exception as e:
        logger.critical(f"Critical Failure: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
