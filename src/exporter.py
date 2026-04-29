import calendar
import logging
import random

import pandas as pd
from colorama import Fore, Style, init

from .config import AppConfig

init(autoreset=True)
logger = logging.getLogger(__name__)


def generate_pastel_color() -> str:
    """Generates a random light pastel color in Hex format."""
    r = random.randint(200, 255)
    g = random.randint(200, 255)
    b = random.randint(200, 255)
    return f"#{r:02X}{g:02X}{b:02X}"


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


def export_formatted_schedule(df: pd.DataFrame, config: AppConfig | None = None):
    """
    Pivots the schedule DataFrame, applies dynamic colors to members,
    and exports it to a formatted Excel file.
    """
    config = config or AppConfig()

    if df.empty:
        logger.warning("Empty schedule dataframe provided. Skipping formatted export.")
        return

    logger.info("Processing formatted schedule...")

    # Ensure date is parsed correctly
    df["date"] = pd.to_datetime(df["date"])

    # Create the Pivot Table
    pivot_df = df.pivot_table(
        index=["date", "event"],
        columns="role",
        values="member_name",
        aggfunc=lambda x: ", ".join(x),
    ).fillna("-")

    # Transform indices into normal columns
    pivot_df.columns.name = None
    pivot_df = pivot_df.reset_index()

    # Determine base month for the title (using the first date)
    base_month = pivot_df["date"].iloc[0].month if not pivot_df.empty else 1
    month_name = calendar.month_name[base_month]

    # Format date for clean display
    pivot_df["date"] = pivot_df["date"].dt.date

    # Terminal Formatting
    print("\n" + "=" * 60)
    print(f"{Fore.GREEN} SCHEDULE PREVIEW {Style.RESET_ALL}")
    print("=" * 60)

    try:
        from tabulate import tabulate

        print(
            tabulate(
                pivot_df, headers="keys", tablefmt="fancy_grid", showindex=False
            )
        )
    except ImportError:
        print(pivot_df.to_string(index=False))
        print(
            f"\n{Fore.YELLOW}Tip: Install 'tabulate' for prettier terminal tables: pip install tabulate{Style.RESET_ALL}"
        )

    # Output path
    output_excel = config.out_dir / "formatted_schedule.xlsx"
    logger.info(f"Exporting to Excel... ({output_excel})")

    config.out_dir.mkdir(parents=True, exist_ok=True)

    # 3. Export to Excel with Merged Title and Automatic Colors
    unique_members = df["member_name"].unique()
    member_colors = {member: generate_pastel_color() for member in unique_members}

    with pd.ExcelWriter(
        output_excel, engine="xlsxwriter", datetime_format="yyyy-mm-dd"
    ) as writer:
        workbook = writer.book

        # startrow=1 frees up the first row (0) for our merged title
        pivot_df.to_excel(writer, sheet_name="Schedule", index=False, startrow=1)
        worksheet = writer.sheets["Schedule"]

        # -- Title Formatting (Merge Cell) --
        title_format = workbook.add_format(
            {
                "bold": True,
                "align": "center",
                "valign": "vcenter",
                "fg_color": "#D9E1F2",
                "border": 1,
                "font_size": 14,
            }
        )

        num_cols = len(pivot_df.columns) - 1
        title_text = f"Schedule - {month_name}"
        
        # Merge from row 0, col 0 to row 0, last col
        worksheet.merge_range(0, 0, 0, num_cols, title_text, title_format)

        # -- Apply Colors (Conditional Formatting) --
        end_row = len(pivot_df) + 1

        for member, hex_color in member_colors.items():
            color_format = workbook.add_format(
                {"bg_color": hex_color, "font_color": "black"}
            )

            # Apply color to all role columns (from column 2 onwards)
            for col_idx in range(2, len(pivot_df.columns)):
                worksheet.conditional_format(
                    2,
                    col_idx,
                    end_row,
                    col_idx,
                    {
                        "type": "cell",
                        "criteria": "==",
                        "value": f'"{member}"',
                        "format": color_format,
                    },
                )

        worksheet.autofit()

    logger.info(f"Success! File ready at: {output_excel}")


def preview_raw(raw_schedule_solution: pd.DataFrame, config: AppConfig | None = None):
    # Backward compatible if still used, but usually export_formatted_schedule covers it
    config = config or AppConfig()
    c = config.cols
    df = pd.DataFrame(raw_schedule_solution)

    cols = [c.DATE, c.EVENT, c.ROLE, c.MEMBER_NAME, c.MEMBER_ID]
    df = df[cols]
    df[c.DATE] = pd.to_datetime(df[c.DATE]).dt.strftime("%d-%m-%Y")

    print("\n--- Schedule Preview ---")
    print(df.head(10).to_markdown(index=False))
