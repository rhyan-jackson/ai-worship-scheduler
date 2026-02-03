import os
from datetime import date
from typing import Dict, List, Set, Tuple

import pandas as pd

from .config import FilesConfig
from .model import AgendaEntry, EventTemplate, Member, RoleDemand, TemplateRule
from .utils import get_key_fingerprint, parse_dates_safely

DEFAULT_DATA_FOLDER = "data"


def load_members(members_csv_filepath: str) -> Tuple[List[Member], Dict[str, int]]:
    """
    Loads members from a csv file structured as:
    id,name,roles,max_shifts

    Returns:
        Tuple containing:
        1. List[Member]: Members registered in the CSV
        3. Dict[(fingerprint, id)]: Match between name fingerprint and id used in another tables
    """
    if not os.path.exists(members_csv_filepath):
        raise FileNotFoundError(f"File not found: {members_csv_filepath}")

    members = []
    fingerprint_map = {}
    df = pd.read_csv(members_csv_filepath)

    for _, row in df.iterrows():
        raw_name = row["name"].strip()
        fingerprint = get_key_fingerprint(raw_name)

        if fingerprint in fingerprint_map:
            raise ValueError(
                f"Name collision detected in members table.\n"
                f"The name '{raw_name}' generates the same fingerprint ('{fingerprint}') as an existing member.\n"
                f"Action Required: Please edit members.csv and make the names distinct\n"
                f"(e.g., add an instrument or nickname)."
            )

        fingerprint_map[fingerprint] = row["id"]

        raw_roles = row["roles"]
        roles = [role.strip() for role in raw_roles.split(";")]
        new_member = Member(
            id=row["id"],
            name=row["name"],
            roles=set(roles),
            max_shifts=row["max_shifts"],
        )
        members.append(new_member)

    print("Members loaded:", members)
    print("Fingerprint map:", fingerprint_map)

    return members, fingerprint_map


def load_unavailability(
    unavailability_csv_filepath: str, fingerprint_map: Dict[str, int]
) -> Set[Tuple[int, date]]:
    if not os.path.exists(unavailability_csv_filepath):
        raise FileNotFoundError(f"File not found: {unavailability_csv_filepath}")
    df = pd.read_csv(unavailability_csv_filepath)
    df = parse_dates_safely(df, "date")

    unavailabilities = set()

    for _, row in df.iterrows():
        raw_name = row["name"]
        day = row["data"]

        search_key = get_key_fingerprint(raw_name)
        if search_key not in fingerprint_map:
            raise ValueError(
                f"Error: Member '{raw_name}' (key: {search_key}) not found in member list."
            )

        member_id = fingerprint_map[search_key]
        unavailabilities.add((member_id, day))

    return unavailabilities


def load_templates(templates_csv_filepath: str) -> Dict[str, EventTemplate]:
    df = pd.read_csv(templates_csv_filepath)
    grouped = df.groupby("event_template")

    templates = {}

    for name, group in grouped:
        rules = []
        for _, row in group.iterrows():
            rules.append(
                TemplateRule(
                    role=row["role"], min_qty=row["min_qty"], max_qty=row["max_qty"]
                )
            )
        templates[name] = EventTemplate(name=str(name), rules=rules)

    print("Templates loaded:", templates)

    return templates


def load_events(events_csv_filepath: str) -> List[AgendaEntry]:
    if not os.path.exists(events_csv_filepath):
        raise FileNotFoundError(f"File not found: {events_csv_filepath}")
    df = pd.read_csv(events_csv_filepath)
    df = parse_dates_safely(df, "date")
    pass


def build_standard_schedule(
    event_csv_filepath: str, template_csv_filepath: str
) -> List[RoleDemand]:
    if not os.path.exists(event_csv_filepath):
        raise FileNotFoundError(f"File not found: {event_csv_filepath}")

    if not os.path.exists(template_csv_filepath):
        raise FileNotFoundError(f"File not found: {template_csv_filepath}")

    events_grouped = load_events(event_csv_filepath)
    templates = load_templates(template_csv_filepath)


def apply_custom_overrides(
    demands: List[RoleDemand], custom_overrides_csv_filepath: str
) -> List[RoleDemand]:
    df = pd.read_csv(custom_overrides_csv_filepath)
    pass


def load_data(
    data_folder: str = DEFAULT_DATA_FOLDER, config: FilesConfig = FilesConfig()
) -> Tuple[List[Member], List[RoleDemand], Set[Tuple[int, date]]]:
    """
    Orchestrates the loading of all project data.

    Args:
        data_folder (str): The directory containing the CSV files.
        config (FilesConfig): File name configuration. Uses English defaults if not provided.

    Returns:
        Tuple containing:
        1. List[Member]: Resources available.
        2. List[RoleDemand]: The slots/jobs that need to be filled.
        3. Dict[(id, date), bool]: Fast lookup for unavailability constraints.
    """
    print(f"Start loading data from {data_folder}")

    path_members = os.path.join(data_folder, config.members_file)
    path_unavailability = os.path.join(data_folder, config.unavailability_file)
    path_schedule = os.path.join(data_folder, config.schedule_file)
    path_templates = os.path.join(data_folder, config.templates_file)
    path_custom = os.path.join(data_folder, config.custom_demands_file)

    members, fingerprint_map = load_members(path_members)

    unavailability_map = load_unavailability(path_unavailability, fingerprint_map)

    base_demands = build_standard_schedule(path_schedule, path_templates)
    final_demands = apply_custom_overrides(base_demands, path_custom)

    print("Data load complete")
    return members, final_demands, unavailability_map


if __name__ == "__main__":
    # load_members("data/membros.csv")
    load_templates("data/templates.csv")
