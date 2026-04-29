import csv
import logging
import unicodedata
from datetime import date, datetime, timedelta
from typing import Dict, Optional

import pandas as pd

from .config import AppConfig, Weekday

logger = logging.getLogger(__name__)


def get_key_fingerprint(name: str) -> str:
    """
    Transforms a raw name string into a canonical fingerprint for safe comparison.

    Normalization Algorithm:
    1. Unicode Normalization (NFD): Decomposes characters (e.g., 'ã' becomes 'a' + '~').
    2. ASCII Encoding: Strips non-ASCII characters (removes the separated diacritics).
    3. Case Folding: Converts to lowercase.
    4. Whitespace Removal: Removes all spaces to handle "John Doe" vs "JohnDoe".

    Args:
        name (str): The raw input name (e.g., "João  Silva").

    Returns:
        str: The normalized key (e.g., "joaosilva").
    """
    if not isinstance(name, str):
        return ""

    nfkd_form = unicodedata.normalize("NFKD", name)
    only_ascii = nfkd_form.encode("ASCII", "ignore").decode("utf-8")

    return only_ascii.lower().replace(" ", "")


def parse_dates_safely(df: pd.DataFrame, column_name: str = "date") -> pd.DataFrame:
    df[column_name] = pd.to_datetime(
        df[column_name], format="%d/%m/%Y", errors="coerce"
    )

    invalid_rows = df[df[column_name].isna()]

    if not invalid_rows.empty:
        bad_indices = invalid_rows.index.tolist()
        raise ValueError(
            f"Date error:\n"
            f"The system could not parse dates in the following rows: {bad_indices}.\n"
            f"Please check for typos or ensure the format is correct (DD/MM/YYYY)."
        )

    df[column_name] = df[column_name].dt.date  # type: ignore

    return df


def parse_date_safely(date_str: str) -> date:
    """Parses a single string date in DD-MM-YYYY format using standard datetime."""
    try:
        return datetime.strptime(date_str, "%d/%m/%Y").date()
    except ValueError:
        raise ValueError(
            f"Invalid date format: '{date_str}'. "
            "Please ensure the format is DD/MM/YYYY."
        ) from None


def generate_schedule_skeleton(
    start_date: date,
    end_date: date,
    config: AppConfig,
    weekday_selection: Optional[Dict[int, str]] = None,
):
    """
    Generates a CSV file with strictly 'date' and 'event_template'.
    """
    if weekday_selection is None:
        weekday_selection = {
            # Weekday.MONDAY: "Segunda",
            # Weekday.TUESDAY: "Terça",
            Weekday.WEDNESDAY: "Quarta",
            # Weekday.THURSDAY: "Quinta",
            # Weekday.FRIDAY: "Sexta",
            # Weekday.SATURDAY: "Sábado",
            Weekday.SUNDAY: "Domingo",
        }

    logger.info(f"Generating schedule skeleton from {start_date} to {end_date}...")

    rows = []
    current_date = start_date

    while current_date <= end_date:
        weekday = current_date.weekday()

        if weekday in weekday_selection:
            template_name = weekday_selection[weekday]

            rows.append(
                {
                    config.cols.DATE: current_date.strftime("%d/%m/%Y"),
                    config.cols.EVENT_TEMPLATE: template_name,
                }
            )

        current_date += timedelta(days=1)

    output_file = config.data_dir / config.schedule_file

    if not output_file.parent.exists():
        output_file.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {output_file.parent}")

    if rows:
        fieldnames = [config.cols.DATE, config.cols.EVENT_TEMPLATE]

        try:
            with open(output_file, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

            logger.info(f"Success! {len(rows)} entries generated in '{output_file}'.")

        except IOError as e:
            logger.error(f"Error writing to file: {e}")
    else:
        logger.warning("No dates found matching the current configuration.")
