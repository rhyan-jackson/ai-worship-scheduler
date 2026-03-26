import csv
import os
from datetime import date, timedelta
from typing import Dict, List

# --- CONFIGURATION ---

# 1. Define the period you want to generate
START_DATE = date(2025, 3, 1)
END_DATE = date(2025, 3, 31)

# 2. Define the days of the week and the Template Name
# 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
WEEKDAY_CONFIG: Dict[int, str] = {
    2: "Quarta",  # Wednesday
    6: "Domingo",  # Sunday
}

# 3. Output file path
OUTPUT_FILE = "data/schedule.csv"


def ensure_directory(file_path: str):
    """Ensures the directory for the output file exists."""
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
        print(f"📁 Created directory: {directory}")


def generate_schedule_skeleton():
    """
    Generates a CSV file with strictly 'date' and 'event_template'.
    """
    print(f"📅 Generating schedule skeleton from {START_DATE} to {END_DATE}...")

    rows = []
    current_date = START_DATE

    while current_date <= END_DATE:
        weekday = current_date.weekday()

        if weekday in WEEKDAY_CONFIG:
            template_name = WEEKDAY_CONFIG[weekday]

            # Strictly the columns you requested
            rows.append(
                {
                    "date": current_date.strftime("%Y-%m-%d"),
                    "event_template": template_name,
                }
            )

        current_date += timedelta(days=1)

    # Write to CSV
    ensure_directory(OUTPUT_FILE)

    if rows:
        # Only date and event_template
        fieldnames = ["date", "event_template"]

        try:
            with open(OUTPUT_FILE, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

            print(f"✅ Success! {len(rows)} entries generated in '{OUTPUT_FILE}'.")

        except IOError as e:
            print(f"❌ Error writing to file: {e}")
    else:
        print("⚠️ No dates found matching the current configuration.")


if __name__ == "__main__":
    generate_schedule_skeleton()
