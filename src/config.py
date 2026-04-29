from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class CsvColumns:
    """
    Central definition of CSV column names.
    Frozen=True ensures they are treated as constants by default.
    """

    # General
    ID: str = "id"
    NAME: str = "name"
    DATE: str = "date"

    # Members File
    ROLES: str = "roles"
    MAX_SHIFTS: str = "max_shifts"

    # Schedule & Templates Files
    EVENT_TEMPLATE: str = "event_template"
    ROLE: str = "role"
    MIN_QTY: str = "min_qty"
    MAX_QTY: str = "max_qty"

    # Exporter Output Columns
    EVENT: str = "event"
    MEMBER_NAME: str = "member_name"
    MEMBER_ID: str = "member_id"


@dataclass
class AppConfig:
    """
    Central Application Configuration.
    """

    # File Names
    members_file: str = "members.csv"
    unavailabilities_file: str = "unavailabilities.csv"
    schedule_file: str = "schedule.csv"
    templates_file: str = "service_templates.csv"
    custom_demands_file: str = "custom_demands.csv"
    output_file: str = "schedule_solution.csv"

    # Directories
    base_dir: Path = Path(__file__).parent.parent
    data_dir: Path = base_dir / "data"
    out_dir: Path = base_dir / "out"
    intermediary_dir: Path = out_dir / "processed"

    # Column Definitions (Nested Configuration)
    cols: CsvColumns = field(default_factory=CsvColumns)
