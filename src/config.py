from dataclasses import dataclass, field


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


@dataclass
class FilesConfig:
    """
    Configuration class defining expected file names and column structure.
    """

    # File Names
    members_file: str = "members.csv"
    unavailabilities_file: str = "unavailabilities.csv"
    schedule_file: str = "schedule.csv"
    templates_file: str = "service_templates.csv"
    custom_demands_file: str = "custom_demands.csv"

    # Column Definitions (Nested Configuration)
    cols: CsvColumns = field(default_factory=CsvColumns)
