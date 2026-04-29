import logging

import pandas as pd

from .config import AppConfig

logger = logging.getLogger(__name__)


def export_raw_result(
    raw_schedule_solution: pd.DataFrame, config: AppConfig | None = None
):
    config = config or AppConfig()
    c = config.cols
    df = pd.DataFrame(raw_schedule_solution)

    # Use the centralized constants
    cols = [c.DATE, c.EVENT, c.ROLE, c.MEMBER_NAME, c.MEMBER_ID]
    df = df[cols]

    df[c.DATE] = pd.to_datetime(df[c.DATE]).dt.strftime("%d-%m-%Y")

    # Pathlib makes it easy to ensure the output directory exists
    config.out_dir.mkdir(parents=True, exist_ok=True)

    filepath = config.out_dir / config.output_file
    df.to_csv(filepath, index=False)
    logger.info(f"Schedule saved to: {filepath}")


def preview_raw(raw_schedule_solution: pd.DataFrame, config: AppConfig | None = None):
    config = config or AppConfig()
    c = config.cols
    df = pd.DataFrame(raw_schedule_solution)

    cols = [c.DATE, c.EVENT, c.ROLE, c.MEMBER_NAME, c.MEMBER_ID]
    df = df[cols]
    df[c.DATE] = pd.to_datetime(df[c.DATE]).dt.strftime("%d-%m-%Y")

    print("\n--- Schedule Preview ---")
    print(df.head(10).to_markdown(index=False))
