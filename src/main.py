import logging
import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).parent.parent))

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
        # Load Data
        members, demands, unavailability = load_data()
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
        schedule = solver.solve()

        # Handle Output
        if not schedule:
            logger.warning(
                "No feasible solution found! Please check constraints or member availability."
            )
        else:
            logger.info(f"Optimization Success! Generated {len(schedule)} assignments.")

            # Export to CSV using Pandas
            df = pd.DataFrame(schedule)
            output_file = "final_schedule.csv"

            # Reorder columns for better reading
            cols = ["date", "event", "role", "member_name", "member_id"]
            df = df[cols]

            df.to_csv(output_file, index=False)
            logger.info(f"Schedule saved to: {output_file}")

            # Optional: Print preview
            print("\n--- Schedule Preview ---")
            print(df.head(10).to_markdown(index=False))

    except Exception as e:
        logger.critical(f"Critical Failure: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
