import logging
from datetime import date
from typing import Dict, List, Set, Tuple

import pandas as pd

from .config import AppConfig
from .model import Event, EventTemplate, Member, RoleDemand, TemplateRule
from .utils import get_key_fingerprint, parse_dates_safely

logger = logging.getLogger(__name__)


class DataLoader:
    """
    Service class responsible for loading and coordinating data ingestion.
    """

    def __init__(self, config: AppConfig | None = None):
        self.config = config or AppConfig()
        self.cols = self.config.cols

    def load_members(self) -> Tuple[List[Member], Dict[str, int]]:
        """
        Loads members from a CSV file.

        Returns:
            Tuple containing:
            1. List[Member]: List of Member objects.
            2. Dict[str, int]: Map of {fingerprint_name: id} for collision detection.
        """
        filepath = self.config.data_dir / self.config.members_file

        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        members = []
        fingerprint_map = {}
        df = pd.read_csv(filepath)

        for _, row in df.iterrows():
            raw_name = str(row[self.cols.NAME]).strip()
            fingerprint = get_key_fingerprint(raw_name)

            if fingerprint in fingerprint_map:
                raise ValueError(
                    f"Name collision detected in members table. "
                    f"Name: '{raw_name}' | Fingerprint: '{fingerprint}'. "
                    f"Action: Edit CSV to ensure distinct names."
                )

            fingerprint_map[fingerprint] = row[self.cols.ID]

            raw_roles = str(row[self.cols.ROLES])
            roles = [role.strip() for role in raw_roles.split(";")]

            new_member = Member(
                id=row[self.cols.ID],
                name=raw_name,
                roles=set(roles),
                max_shifts=row[self.cols.MAX_SHIFTS],
            )
            members.append(new_member)

        logger.info(f"Loaded {len(members)} members.")
        return members, fingerprint_map

    def load_unavailability(
        self, fingerprint_map: Dict[str, int]
    ) -> Set[Tuple[int, date]]:
        """
        Loads specific unavailability dates for members.

        Args:
            fingerprint_map (Dict[str, int]): Mapping to resolve names to member IDs.

        Returns:
            Set[Tuple[int, date]]: A set of (member_id, date) tuples.
        """
        filepath = self.config.data_dir / self.config.unavailabilities_file

        if not filepath.exists():
            logger.warning(
                f"Unavailability file not found: {filepath}. Assuming no blocks."
            )
            return set()

        df = pd.read_csv(filepath)
        df = parse_dates_safely(df, self.cols.DATE)

        unavailabilities = set()

        for _, row in df.iterrows():
            raw_name = str(row[self.cols.NAME])
            day = row[self.cols.DATE]

            search_key = get_key_fingerprint(raw_name)
            if search_key not in fingerprint_map:
                raise ValueError(
                    f"Member '{raw_name}' found in unavailability list but not in members file."
                )

            member_id = fingerprint_map[search_key]
            unavailabilities.add((member_id, day))

        logger.info(f"Loaded {len(unavailabilities)} unavailability blocks.")
        return unavailabilities

    def load_templates(self) -> Dict[str, EventTemplate]:
        """
        Loads service templates defining roles and quantities.

        Returns:
            Dict[str, EventTemplate]: Dictionary mapping template names to rule definitions.
        """
        filepath = self.config.data_dir / self.config.templates_file

        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        df = pd.read_csv(filepath)
        grouped = df.groupby(self.cols.EVENT_TEMPLATE)

        templates = {}

        for name, group in grouped:
            rules = []
            for _, row in group.iterrows():
                rules.append(
                    TemplateRule(
                        role=row[self.cols.ROLE],
                        min_qty=int(row[self.cols.MIN_QTY]),
                        max_qty=int(row[self.cols.MAX_QTY]),
                    )
                )
            clean_name = str(name).strip()
            templates[clean_name] = EventTemplate(name=clean_name, rules=rules)

        logger.info(f"Loaded {len(templates)} templates.")
        return templates

    def load_events(self) -> List[Event]:
        """
        Loads the schedule of events to be planned.

        Returns:
            List[Event]: Chronologically sorted list of events.
        """
        filepath = self.config.data_dir / self.config.schedule_file

        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        df = pd.read_csv(filepath)
        df = parse_dates_safely(df, self.cols.DATE)

        events = []
        for _, row in df.iterrows():
            events.append(
                Event(
                    date=row[self.cols.DATE],
                    event_template=str(row[self.cols.EVENT_TEMPLATE]).strip(),
                )
            )

        return sorted(events, key=lambda x: x.date)

    def build_standard_schedule(
        self, events_list: List[Event], templates_map: Dict[str, EventTemplate]
    ) -> List[RoleDemand]:
        """
        Generates the list of role demands by applying templates to the scheduled events.

        Args:
            events_list (List[Event]): The list of scheduled events.
            templates_map (Dict[str, EventTemplate]): Definitions of event requirements.

        Returns:
            List[RoleDemand]: Flat list of all slots needed.
        """
        demands = []
        for event in events_list:
            template = templates_map.get(event.event_template)
            if not template:
                raise ValueError(
                    f"Configuration Error: Event on {event.date} calls for template "
                    f"'{event.event_template}', but it is not defined in templates file."
                )

            for rule in template.rules:
                if rule.max_qty > 1:
                    for i in range(1, rule.max_qty + 1):
                        slot_min_qty = 1 if i <= rule.min_qty else 0
                        demands.append(
                            RoleDemand(
                                date=event.date,
                                event_type=template.name,
                                role=f"{rule.role} {i}",
                                base_role=rule.role,
                                min_qty=slot_min_qty,
                                max_qty=1,
                                source="Template",
                            )
                        )
                else:
                    demands.append(
                        RoleDemand(
                            date=event.date,
                            event_type=template.name,
                            role=f"{rule.role} 1",
                            base_role=rule.role,
                            min_qty=rule.min_qty,
                            max_qty=rule.max_qty,
                            source="Template",
                        )
                    )

        return demands

    def apply_custom_overrides(self, demands: List[RoleDemand]) -> List[RoleDemand]:
        """
        Applies manual overrides (add/remove/modify) to the generated schedule.
        """
        # Logic to be implemented
        return demands

    def load_all(self) -> Tuple[List[Member], List[RoleDemand], Set[Tuple[int, date]]]:
        """
        Orchestrates the loading of all project data.

        Returns:
            Tuple containing Members, Demands, and Unavailabilities.
        """
        logger.info(f"Start loading data from {self.config.data_dir}")

        members_list, fingerprint_map = self.load_members()

        unavailability_map = self.load_unavailability(fingerprint_map)

        templates_map = self.load_templates()
        events_list = self.load_events()

        base_demands = self.build_standard_schedule(events_list, templates_map)
        final_demands = self.apply_custom_overrides(base_demands)

        logger.info(
            f"Data load complete. Members: {len(members_list)}, "
            f"Demands: {len(final_demands)}"
        )
        return members_list, final_demands, unavailability_map


def load_data(
    config: AppConfig | None = None,
) -> Tuple[List[Member], List[RoleDemand], Set[Tuple[int, date]]]:
    """
    Wrapper function for backward compatibility.
    """
    loader = DataLoader(config=config)
    return loader.load_all()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    load_data()
