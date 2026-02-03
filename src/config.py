from dataclasses import dataclass


@dataclass
class FilesConfig:
    """
    Configuration class defining the expected file names.
    Defaults are set to English standard names.
    """

    members_file: str = "members.csv"
    unavailabilities_file: str = "unavailabilities.csv"
    schedule_file: str = "schedule.csv"
    templates_file: str = "service_templates.csv"
    custom_demands_file: str = "custom_demands.csv"
