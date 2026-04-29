import logging
from datetime import date
from typing import Dict

from .config import AppConfig, Weekday
from .utils import generate_schedule_skeleton

# Define the period you want to generate
START_DATE = date(2026, 5, 4)
END_DATE = date(2026, 6, 7)

# Define the days of the week and the Template Name
WEEKDAY_CONFIG: Dict[int, str] = {
    # Weekday.MONDAY: "Segunda",
    # Weekday.TUESDAY: "Terça",
    Weekday.WEDNESDAY: "Quarta",
    # Weekday.THURSDAY: "Quinta",
    # Weekday.FRIDAY: "Sexta",
    # Weekday.SATURDAY: "Sábado",
    Weekday.SUNDAY: "Domingo",
}


def main():
    config = AppConfig()

    # Call the imported function from utils.py
    generate_schedule_skeleton(
        start_date=START_DATE,
        end_date=END_DATE,
        config=config,
        weekday_selection=WEEKDAY_CONFIG,
    )


if __name__ == "__main__":
    # Setup basic logging to see the output in the terminal
    logging.basicConfig(level=logging.INFO)
    main()
